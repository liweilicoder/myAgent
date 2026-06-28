import hashlib
import os
import re
import time
import json
from typing import List, Dict, Optional, Any

import josie_agents.utils.log as log
from josie_agents.core.database_config import get_database_config
from josie_agents.core.josie_llm import JosieLLM
from josie_agents.memory.embedding import get_dimension, get_text_embedder
from josie_agents.memory.storage.qdrant_store import QdrantVectorStore, QdrantConnectionManager

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

try:
    from langdetect import detect
except ImportError:
    detect = None

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None


def _query_preview(text: str, max_len: int = 80) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."

def _get_markitdown_instance():
    """
    Get a configured MarkItDown instance for document conversion.
    """
    if MarkItDown is None:
        log.warn("📄 [RAG] MarkItDown not available. Install with: pip install markitdown")
        return None
    try:
        return MarkItDown()
    except Exception as e:
        log.warn(f"📄 [RAG] MarkItDown unavailable: error={e}")
        return None



def _is_markitdown_supported_format(path: str) -> bool:
    """
    Check if the file format is supported by MarkItDown.
    Supports: PDF, Office docs (docx, xlsx, pptx), images (jpg, png, gif, bmp, tiff),
    audio (mp3, wav, m4a), HTML, text formats (txt, md, csv, json, xml), ZIP files, etc.
    """
    ext = (os.path.splitext(path)[1] or '').lower()
    supported_formats = {
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Text formats
        '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm',
        # Images (OCR + metadata)
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
        # Audio (transcription + metadata)
        '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg',
        # Archives
        '.zip', '.tar', '.gz', '.rar',
        # Code files
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.css', '.scss',
        # Other text
        '.log', '.conf', '.ini', '.cfg', '.yaml', '.yml', '.toml'
    }
    return ext in supported_formats


def _convert_to_markdown(path: str) -> str:
    """
    Universal document reader using MarkItDown with enhanced PDF processing.
    Converts any supported file format to markdown text.
    """
    if not os.path.exists(path):
        log.warn(f"📄 [RAG] convert skipped: file_not_found path={path}")
        return ""

    # 对PDF文件使用增强处理
    ext = (os.path.splitext(path)[1] or '').lower()
    if ext == '.pdf':
        return _enhanced_pdf_processing(path)

    # 其他格式使用原有MarkItDown
    md_instance = _get_markitdown_instance()
    if md_instance is None:
        log.warn(f"📄 [RAG] MarkItDown unavailable, using fallback reader: path={path}")
        return _fallback_text_reader(path)

    try:
        t0 = time.time()
        result = md_instance.convert(path)
        text = getattr(result, "text_content", None)
        if isinstance(text, str) and text.strip():
            log.success(
                f"📄 [RAG] convertToMarkdown done: path={path}, ext={ext or 'unknown'}, "
                f"chars={len(text)}, elapsed_ms={int((time.time() - t0) * 1000)}"
            )
            return text
        log.warn(f"📄 [RAG] MarkItDown returned empty content: path={path}, ext={ext or 'unknown'}")
        return ""
    except Exception as e:
        log.warn(f"📄 [RAG] MarkItDown failed, using fallback reader: path={path}, error={e}")
        return _fallback_text_reader(path)


def _enhanced_pdf_processing(path: str) -> str:
    """
    Enhanced PDF processing with post-processing cleanup.
    """
    log.debug(f"📕 [RAG] pdf_convert start: path={path}")

    # 使用原有MarkItDown提取
    md_instance = _get_markitdown_instance()
    if md_instance is None:
        log.warn(f"📕 [RAG] PDF MarkItDown unavailable, skip unsafe raw PDF read: path={path}")
        return ""

    try:
        t0 = time.time()
        result = md_instance.convert(path)
        raw_text = getattr(result, "text_content", None)
        if not raw_text or not raw_text.strip():
            log.warn(f"📕 [RAG] pdf_convert empty: path={path}")
            return ""

        # 后处理：清理和重组文本
        cleaned_text = _post_process_pdf_text(raw_text)
        if not _is_extracted_pdf_text_usable(cleaned_text):
            log.warn(
                f"📕 [RAG] pdf_convert rejected unsafe extracted text: path={path}, "
                f"raw_chars={len(raw_text)}, cleaned_chars={len(cleaned_text)}"
            )
            return ""

        log.info(
            f"📕 [RAG] pdf_convert done: path={path}, raw_chars={len(raw_text)}, "
            f"cleaned_chars={len(cleaned_text)}, elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return cleaned_text

    except Exception as e:
        log.warn(f"📕 [RAG] pdf_convert failed, skip unsafe raw PDF read: path={path}, error={e}")
        return ""


def _post_process_pdf_text(text: str) -> str:
    """
    Post-process PDF text to improve quality.
    """

    # 1. 按行分割并清理
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 移除单个字符的行（通常是噪音）
        if len(line) <= 2 and not line.isdigit():
            continue

        # 移除明显的页眉页脚噪音
        if re.match(r'^\d+$', line):  # 纯数字行（页码）
            continue
        if line.lower() in ['github', 'project', 'forks', 'stars', 'language']:
            continue

        cleaned_lines.append(line)

    # 2. 智能合并短行
    merged_lines = []
    i = 0

    while i < len(cleaned_lines):
        current_line = cleaned_lines[i]

        # 如果当前行很短，尝试与下一行合并
        if len(current_line) < 60 and i + 1 < len(cleaned_lines):
            next_line = cleaned_lines[i + 1]

            # 合并条件：都是内容，不是标题
            if (not current_line.endswith('：') and
                    not current_line.endswith(':') and
                    not current_line.startswith('#') and
                    not next_line.startswith('#') and
                    len(next_line) < 120):
                merged_line = current_line + " " + next_line
                merged_lines.append(merged_line)
                i += 2  # 跳过下一行
                continue

        merged_lines.append(current_line)
        i += 1

    # 3. 重新组织段落
    paragraphs = []
    current_paragraph = []

    for line in merged_lines:
        # 检查是否是新段落的开始
        if (line.startswith('#') or  # 标题
                line.endswith('：') or  # 中文冒号结尾
                line.endswith(':') or  # 英文冒号结尾
                len(line) > 150 or  # 长句通常是段落开始
                not current_paragraph):  # 第一行

            # 保存当前段落
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []

            paragraphs.append(line)
        else:
            current_paragraph.append(line)

    # 添加最后一个段落
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))

    return '\n\n'.join(paragraphs)

def _is_extracted_pdf_text_usable(text: str) -> bool:
    """
    Reject PDF internals masquerading as extracted text.
    """
    if not text or not text.strip():
        return False

    lowered = text.lower()
    pdf_stream_markers = (
        "/flatedecode",
        "flatedecode",
        "endstream",
        "endobj",
        " obj",
        "xref",
        "trailer",
        "startxref",
    )
    marker_hits = sum(1 for marker in pdf_stream_markers if marker in lowered)
    if marker_hits >= 2:
        return False

    total_chars = len(text)
    control_chars = sum(
        1
        for ch in text
        if ord(ch) < 32 and ch not in ("\n", "\r", "\t")
    )
    if total_chars and control_chars / total_chars > 0.01:
        return False

    printable_chars = sum(1 for ch in text if ch.isprintable() or ch in ("\n", "\r", "\t"))
    if total_chars and printable_chars / total_chars < 0.95:
        return False

    return True

def _fallback_text_reader(path: str) -> str:
    """
    Simple fallback reader for basic text files when MarkItDown is unavailable.
    """
    if (os.path.splitext(path)[1] or '').lower() == '.pdf':
        log.warn(f"🧯 [RAG] fallback reader skipped for PDF to avoid binary stream pollution: path={path}")
        return ""

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            log.debug(f"🧯 [RAG] fallback reader done: path={path}, encoding=utf-8, chars={len(text)}")
            return text
    except Exception as e:
        log.debug(f"🧯 [RAG] fallback reader utf-8 failed: path={path}, error={e}")
        try:
            with open(path, 'r', encoding='latin-1', errors='ignore') as f:
                text = f.read()
                log.debug(f"🧯 [RAG] fallback reader done: path={path}, encoding=latin-1, chars={len(text)}")
                return text
        except Exception as e2:
            log.error(f"🧯 [RAG] fallback reader failed: path={path}, error={e2}")
            return ""



def _detect_lang(sample: str) -> str:
    if detect is None:
        return "unknown"
    try:
        return detect(sample[:1000]) if sample else "unknown"
    except Exception:
        return "unknown"


def _is_cjk(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF or
        0x3400 <= code <= 0x4DBF or
        0x20000 <= code <= 0x2A6DF or
        0x2A700 <= code <= 0x2B73F or
        0x2B740 <= code <= 0x2B81F or
        0x2B820 <= code <= 0x2CEAF or
        0xF900 <= code <= 0xFAFF
    )


def _approx_token_len(text: str) -> int:
    # 近似估计：CJK字符按1 token，其他按空白分词
    cjk = sum(1 for ch in text if _is_cjk(ch))
    non_cjk_tokens = len([t for t in text.split() if t])
    return cjk + non_cjk_tokens


def _split_paragraphs_with_headings(text: str) -> List[Dict]:
    log.debug(f" 🌟[RAG] split_paragraphs_with_headings start: {text[:500]}")
    lines = text.splitlines()
    heading_stack: List[str] = []
    paragraphs: List[Dict] = []
    buf: List[str] = []
    char_pos = 0

    def flush_buf(end_pos: int):
        if not buf:
            return
        content = "\n".join(buf).strip()
        if not content:
            return
        paragraphs.append({
            "content": content,
            "heading_path": " > ".join(heading_stack) if heading_stack else None,
            "start": max(0, end_pos - len(content)),
            "end": end_pos,
        })

    for ln in lines:
        raw = ln
        stripped = raw.strip()
        if stripped.startswith("#"):
            # heading line
            flush_buf(char_pos)
            level = len(raw) - len(raw.lstrip('#'))
            title = raw.lstrip('#').strip()
            if level <= 0:
                level = 1
            if level <= len(heading_stack):
                heading_stack = heading_stack[:level-1]
            heading_stack.append(title)
            char_pos += len(raw) + 1
            continue
        # paragraph accumulation
        is_markdown_rule = (
            len(stripped) >= 3 and
            len(set(stripped)) == 1 and
            stripped[0] in "-*_"
        )
        if stripped == "" or is_markdown_rule:
            flush_buf(char_pos)
            buf = []
        else:
            buf.append(raw)
        char_pos += len(raw) + 1
    flush_buf(char_pos)
    if not paragraphs:
        paragraphs = [{"content": text, "heading_path": None, "start": 0, "end": len(text)}]

    log.debug(f"🌟[RAG] split_paragraphs_with_headings finish, paragraph_num={len(paragraphs)}, ret={json.dumps(paragraphs, indent=4, ensure_ascii=False)}")
    return paragraphs


def _chunk_paragraphs(paragraphs: List[Dict], chunk_tokens: int, overlap_tokens: int) -> List[Dict]:

    log.debug(f"🌟[RAG] _chunk_paragraphs start: paragraphs_num={len(paragraphs)}, chunk_tokens={chunk_tokens}, overlap_tokens={overlap_tokens}")
    chunks: List[Dict] = []
    cur: List[Dict] = []
    cur_tokens = 0
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        p_tokens = _approx_token_len(p["content"]) or 1
        if cur_tokens + p_tokens <= chunk_tokens or not cur:
            cur.append(p)
            cur_tokens += p_tokens
            i += 1
        else:
            # emit current chunk
            log.debug(f"🌟[RAG] merge paragraphs start, paragraphs_num={len(cur)}, paragraphs={json.dumps(cur, indent=4, ensure_ascii=False)}")

            content = "\n\n".join(x["content"] for x in cur)
            start = cur[0]["start"]
            end = cur[-1]["end"]
            heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)
            chunks.append({
                "content": content,
                "start": start,
                "end": end,
                "heading_path": heading_path,
            })
            # build overlap by keeping tail tokens
            if overlap_tokens > 0 and cur:
                kept: List[Dict] = []
                kept_tokens = 0
                for x in reversed(cur):
                    t = _approx_token_len(x["content"]) or 1
                    if kept_tokens + t > overlap_tokens:
                        break
                    kept.append(x)
                    kept_tokens += t
                p_tokens = _approx_token_len(paragraphs[i]["content"]) or 1
                if kept_tokens and kept_tokens + p_tokens <= chunk_tokens:
                    cur = list(reversed(kept))
                    cur_tokens = kept_tokens
                else:
                    cur = []
                    cur_tokens = 0
            else:
                cur = []
                cur_tokens = 0
    if cur:
        log.debug(f"🌟[RAG] merge paragraphs start, paragraphs_num={len(cur)}, paragraphs={json.dumps(cur, indent=4, ensure_ascii=False)}")

        content = "\n\n".join(x["content"] for x in cur)
        start = cur[0]["start"]
        end = cur[-1]["end"]
        heading_path = next((x["heading_path"] for x in reversed(cur) if x.get("heading_path")), None)
        chunks.append({
            "content": content,
            "start": start,
            "end": end,
            "heading_path": heading_path,
        })

    log.debug(f"🌟[RAG] _chunk_paragraphs done: chunks={json.dumps(chunks, indent=4, ensure_ascii=False)}")
    return chunks


def load_and_chunk_texts(paths: List[str], chunk_size: int = 800, chunk_overlap: int = 100,
                         namespace: Optional[str] = None, source_label: str = "rag") -> List[Dict]:
    """
    Universal document loader and chunker using MarkItDown.
    Converts all supported formats to markdown, then chunks intelligently.
    """
    t0 = time.time()
    log.debug(
        f"🧩 [RAG] load_and_chunk start: files_num={len(paths)}, chunk_size={chunk_size}, "
        f"overlap={chunk_overlap}, namespace={namespace or 'default'}"
    )
    chunks: List[Dict] = []
    seen_hashes = set()
    skipped_files = 0
    duplicate_chunks = 0

    for path in paths:
        if not os.path.exists(path):
            skipped_files += 1
            log.warn(f"🧩 [RAG] load skipped: reason=file_not_found, path={path}")
            continue

        file_t0 = time.time()
        before_chunks = len(chunks)
        log.debug(f"🧩 [RAG] load file start: path={path}")
        ext = (os.path.splitext(path)[1] or '').lower()
        if not _is_markitdown_supported_format(path):
            log.warn(f"🧩 [RAG] unsupported extension, trying converter anyway: path={path}, ext={ext or 'unknown'}")

        # Convert to markdown using MarkItDown
        markdown_text = _convert_to_markdown(path)
        if not markdown_text.strip():
            skipped_files += 1
            log.warn(f"🧩 [RAG] load skipped: reason=empty_content, path={path}")
            continue

        lang = _detect_lang(markdown_text)
        doc_id = hashlib.md5(f"{path}|{len(markdown_text)}".encode('utf-8')).hexdigest()

        # Always use markdown-aware chunking for better structure preservation
        para = _split_paragraphs_with_headings(markdown_text)
        token_chunks = _chunk_paragraphs(para, chunk_tokens=max(1, chunk_size), overlap_tokens=max(0, chunk_overlap))

        for ch in token_chunks:
            content = ch["content"]
            start = ch.get("start", 0)
            end = ch.get("end", start + len(content))
            norm = content.strip()
            if not norm:
                continue

            content_hash = hashlib.md5(norm.encode('utf-8')).hexdigest()
            if content_hash in seen_hashes:
                duplicate_chunks += 1
                continue
            seen_hashes.add(content_hash)

            chunk_id = hashlib.md5(f"{doc_id}|{start}|{end}|{content_hash}".encode('utf-8')).hexdigest()
            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": {
                    "source_path": path,
                    "file_ext": ext,
                    "doc_id": doc_id,
                    "lang": lang,
                    "start": start,
                    "end": end,
                    "content_hash": content_hash,
                    "namespace": namespace or "default",
                    "source": source_label,
                    "external": True,
                    "heading_path": ch.get("heading_path"),
                    "format": "markdown",  # Mark all content as markdown-processed
                },
            })

        log.info(
            f"🧩 [RAG] load file done: path={path}, doc_id={doc_id}, lang={lang}, "
            f"chars={len(markdown_text)}, chunks={len(chunks) - before_chunks}, "
            f"elapsed_ms={int((time.time() - file_t0) * 1000)}"
        )

    log.info(
        f"🧩 [RAG] load_and_chunk done: files={len(paths)}, skipped_files={skipped_files}, "
        f"chunks={len(chunks)}, duplicate_chunks={duplicate_chunks}, "
        f"elapsed_ms={int((time.time() - t0) * 1000)}"
    )
    return chunks


def build_graph_from_chunks(neo4j, chunks: List[Dict]) -> None:
    log.info(f"🕸️ [RAG] graph_build start: chunks={len(chunks)}")
    created_docs = set()
    created_chunks = 0
    failed_ops = 0
    for ch in chunks:
        mem_id = ch["id"]
        meta = ch.get("metadata", {})
        source_path = meta.get("source_path")
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in created_docs:
            created_docs.add(doc_id)
            try:
                neo4j.add_entity(
                    entity_id=doc_id,
                    name=os.path.basename(source_path or doc_id),
                    entity_type="Document",
                    properties={"source_path": source_path, "lang": meta.get("lang")}
                )
            except Exception:
                failed_ops += 1
                log.debug(f"🕸️ [RAG] graph document entity skipped: doc_id={doc_id}")
        try:
            neo4j.add_entity(entity_id=mem_id, name=mem_id, entity_type="Memory", properties={
                "source_path": source_path,
                "doc_id": doc_id,
                "start": meta.get("start"),
                "end": meta.get("end"),
            })
            created_chunks += 1
        except Exception:
            failed_ops += 1
            log.debug(f"🕸️ [RAG] graph memory entity skipped: memory_id={mem_id}")
        if doc_id:
            try:
                neo4j.add_relationship(from_id=doc_id, to_id=mem_id, rel_type="HAS_CHUNK", properties={})
            except Exception:
                failed_ops += 1
                log.debug(f"🕸️ [RAG] graph relationship skipped: doc_id={doc_id}, memory_id={mem_id}")
    log.info(
        f"🕸️ [RAG] graph_build done: docs={len(created_docs)}, chunks={created_chunks}, "
        f"failed_ops={failed_ops}"
    )


def _preprocess_markdown_for_embedding(text: str) -> str:
    """
    Preprocess markdown text for better embedding quality.
    Removes excessive markup while preserving semantic content.
    """
    log.debug(f"[RAG] _preprocess_markdown_for_embedding, text={text[:100]}...")

    # Remove markdown headers symbols but keep the text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove markdown links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove markdown emphasis markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # italic
    text = re.sub(r'`([^`]+)`', r'\1', text)  # inline code

    # Remove markdown code blocks but keep content
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', r'\1', text)

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def _create_default_vector_store(dimension: int = None) -> QdrantVectorStore:
    """
    Create default Qdrant vector store with RAG-optimized settings.
    使用连接管理器避免重复连接。
    """
    # 获取数据库配置
    db_config = get_database_config()

    # 初始化Qdrant向量数据库（使用连接管理器避免重复连接）
    qdrant_config = db_config.get_qdrant_config() or {}
    qdrant_config["vector_size"] = get_dimension()
    log.debug(
        f"🗄️ [RAG] vector_store create done: collection={qdrant_config.get('collection_name', 'default')}, "
        f"dimension={qdrant_config['vector_size']}"
    )
    return QdrantConnectionManager.get_instance(**qdrant_config)

# Cache functions removed - using unified embedder with internal caching


def index_chunks(
    store=None,
    chunks: List[Dict] = None,
    cache_db: Optional[str] = None,
    batch_size: int = 10,
    rag_namespace: str = "default"
) -> None:
    """
    Index markdown chunks with unified embedding and Qdrant storage.
    Uses百炼 API with fallback to sentence-transformers.
    """
    if not chunks:
        log.warn("🧠 [RAG] No chunks to index")
        return

    t0 = time.time()
    log.debug(
        f"🧠 [RAG] index chunks start: chunks_num={len(chunks)}, batch_size={batch_size}, "
        f"namespace={rag_namespace}"
    )

    # Use unified embedding from embedding module
    embedder = get_text_embedder()
    dimension = get_dimension(384)

    # Create default Qdrant store if not provided
    if store is None:
        store = _create_default_vector_store(dimension)
        log.debug(f"🗄️ [RAG] index chunks using default vector_store: dimension={dimension}")

    # Preprocess markdown texts for better embeddings
    processed_texts = []
    for c in chunks:
        raw_content = c["content"]
        processed_content = _preprocess_markdown_for_embedding(raw_content)
        processed_texts.append(processed_content)

    log.debug(f"🧠 [RAG] embedding start: total_texts={len(processed_texts)}, batch_size={batch_size}, dimension={dimension}")

    # Batch encoding with unified embedder
    vecs: List[List[float]] = []
    for i in range(0, len(processed_texts), batch_size):
        part = processed_texts[i:i + batch_size]
        batch_t0 = time.time()
        try:
            # Use unified embedder directly (handles caching internally)
            part_vecs = embedder.encode(part)

            # Normalize to List[List[float]]
            if not isinstance(part_vecs, list):
                # 单个numpy数组转为列表中的列表
                if hasattr(part_vecs, "tolist"):
                    part_vecs = [part_vecs.tolist()]
                else:
                    part_vecs = [list(part_vecs)]
            else:
                # 检查是否是嵌套列表
                if part_vecs and not isinstance(part_vecs[0], (list, tuple)) and hasattr(part_vecs[0], "__len__"):
                    # numpy数组列表 -> 转换每个数组
                    normalized_vecs = []
                    for v in part_vecs:
                        if hasattr(v, "tolist"):
                            normalized_vecs.append(v.tolist())
                        else:
                            normalized_vecs.append(list(v))
                    part_vecs = normalized_vecs
                elif part_vecs and not isinstance(part_vecs[0], (list, tuple)):
                    # 单个向量被误判为列表，实际应该包装成[[...]]
                    if hasattr(part_vecs, "tolist"):
                        part_vecs = [part_vecs.tolist()]
                    else:
                        part_vecs = [list(part_vecs)]

            for v in part_vecs:
                try:
                    # 确保向量是float列表
                    if hasattr(v, "tolist"):
                        v = v.tolist()
                    v_norm = [float(x) for x in v]
                    if len(v_norm) != dimension:
                        log.warn(f"🧠 [RAG] embedding vector dimension mismatch: expected={dimension}, actual={len(v_norm)}")
                        # 用零向量填充或截断
                        if len(v_norm) < dimension:
                            v_norm.extend([0.0] * (dimension - len(v_norm)))
                        else:
                            v_norm = v_norm[:dimension]
                    vecs.append(v_norm)
                except Exception as e:
                    log.warn(f"🧠 [RAG] embedding vector conversion failed, using zero vector: error={e}")
                    vecs.append([0.0] * dimension)

        except Exception as e:
            log.warn(f"🧠 [RAG] embedding batch failed: batch_start={i}, batch_size={len(part)}, error={e}")
            log.warn(f"🧠 [RAG] embedding retry with smaller batches: batch_start={i}")

            # 尝试重试：将批次分解为更小的块
            success = False
            for j in range(0, len(part), 8):  # 更小的批次
                small_part = part[j:j + 8]
                try:
                    time.sleep(2)  # 等待2秒避免频率限制

                    small_vecs = embedder.encode(small_part)
                    # Normalize to List[List[float]]
                    if isinstance(small_vecs, list) and small_vecs and not isinstance(small_vecs[0], list):
                        small_vecs = [small_vecs]

                    for v in small_vecs:
                        if hasattr(v, "tolist"):
                            v = v.tolist()
                        try:
                            v_norm = [float(x) for x in v]
                            if len(v_norm) != dimension:
                                log.warn(
                                    f"🧠 [RAG] embedding vector dimension mismatch: "
                                    f"expected={dimension}, actual={len(v_norm)}"
                                )
                                if len(v_norm) < dimension:
                                    v_norm.extend([0.0] * (dimension - len(v_norm)))
                                else:
                                    v_norm = v_norm[:dimension]
                            vecs.append(v_norm)
                            success = True
                        except Exception as e2:
                            log.warn(f"🧠 [RAG] embedding small batch vector conversion failed, using zero vector: error={e2}")
                            vecs.append([0.0] * dimension)
                except Exception as e2:
                    log.warn(f"🧠 [RAG] embedding small batch failed: batch_start={i + j}, batch_size={len(small_part)}, error={e2}")
                    # 为这个小批次创建零向量
                    for _ in range(len(small_part)):
                        vecs.append([0.0] * dimension)

            if not success:
                log.error(f"🧠 [RAG] embedding batch exhausted fallback: batch_start={i}, zero_vectors={len(part)}")

        log.debug(
            f"🧠 [RAG] embedding batch done: progress={min(i + batch_size, len(processed_texts))}/"
            f"{len(processed_texts)}, elapsed_ms={int((time.time() - batch_t0) * 1000)}"
        )

    # Prepare metadata with RAG tags
    metas: List[Dict] = []
    ids: List[str] = []
    for ch in chunks:
        meta = {
            "memory_id": ch["id"],
            "user_id": "rag_user",
            "memory_type": "rag_chunk",
            "content": ch["content"],  # Keep original markdown content
            "data_source": "rag_pipeline",  # RAG identification tag
            "rag_namespace": rag_namespace,
            "is_rag_data": True,  # Clear RAG data marker
        }
        # Merge chunk metadata
        meta.update(ch.get("metadata", {}))
        metas.append(meta)
        ids.append(ch["id"])

    log.debug(f"🗄️ [RAG] qdrant upsert start: vectors={len(vecs)}, metadata={len(metas)}, namespace={rag_namespace}")
    success = store.add_vectors(vectors=vecs, metadata=metas, ids=ids)
    if success:
        log.info(
            f"🧠 [RAG] index chunks done: vectors={len(vecs)}, namespace={rag_namespace}, "
            f"elapsed_ms={int((time.time() - t0) * 1000)}"
        )
    else:
        log.error(f"🗄️ [RAG] qdrant upsert failed: vectors={len(vecs)}, namespace={rag_namespace}")
        raise RuntimeError("Failed to index vectors to Qdrant")


def embed_query(query: str) -> List[float]:
    """
    Embed query using unified embedding (百炼 with fallback).
    """
    embedder = get_text_embedder()
    dimension = get_dimension(384)
    try:
        t0 = time.time()
        vec = embedder.encode(query)

        # Normalize to List[float]
        if hasattr(vec, "tolist"):
            vec = vec.tolist()

        # 处理嵌套列表情况
        if isinstance(vec, list) and vec and isinstance(vec[0], (list, tuple)):
            vec = vec[0]  # Extract first vector if nested

        # 转换为float列表
        result = [float(x) for x in vec]

        # 检查维度
        if len(result) != dimension:
            log.warn(f"🔎 [RAG] query vector dimension mismatch: expected={dimension}, actual={len(result)}")
            # 用零向量填充或截断
            if len(result) < dimension:
                result.extend([0.0] * (dimension - len(result)))
            else:
                result = result[:dimension]

        log.debug(
            f"🔎 [RAG] query_embedding done: query='{_query_preview(query)}', "
            f"dimension={len(result)}, elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return result
    except Exception as e:
        log.error(f"🔎 [RAG] query_embedding failed: query='{_query_preview(query)}', error={e}")
        # Return zero vector as fallback
        return [0.0] * dimension


def search_vectors(
    store=None,
    query: str = "",
    top_k: int = 8,
    rag_namespace: Optional[str] = None,
    only_rag_data: bool = True,
    score_threshold: Optional[float] = None
) -> List[Dict]:
    """
    Search RAG vectors using unified embedding and Qdrant.
    """
    if not query:
        log.warn("🔎 [RAG] search skipped: empty_query")
        return []

    # Create default store if not provided
    if store is None:
        store = _create_default_vector_store()

    # Embed query with unified embedder
    qv = embed_query(query)

    # Build filter for RAG data
    where = {"memory_type": "rag_chunk"}
    if only_rag_data:
        where["is_rag_data"] = True
        where["data_source"] = "rag_pipeline"
    if rag_namespace:
        where["rag_namespace"] = rag_namespace

    try:
        t0 = time.time()
        log.debug(
            f"🔎 [RAG] vector_search start: query='{_query_preview(query)}', top_k={top_k}, "
            f"threshold={score_threshold}, namespace={rag_namespace or 'all'}, only_rag_data={only_rag_data}"
        )
        results = store.search_similar(
            query_vector=qv,
            limit=top_k,
            score_threshold=score_threshold,
            where=where
        )
        log.debug(
            f"🔎 [RAG] vector_search done: hits={len(results)}, top_k={top_k}, "
            f"elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return results
    except Exception as e:
        log.error(f"🔎 [RAG] vector_search failed: query='{_query_preview(query)}', error={e}")
        return []


def _prompt_mqe(query: str, n: int) -> List[str]:
    try:
        t0 = time.time()
        llm = JosieLLM()
        prompt = [
            {"role": "system",
             "content": "你是检索查询扩展助手。生成语义等价或互补的多样化查询。使用中文，简短，避免标点。"},
            {"role": "user", "content": f"原始查询：{query}\n请给出{n}个不同表述的查询，每行一个。"}
        ]
        text = clean_llm_resp(llm.invoke(prompt))

        lines = [ln.strip("- \t") for ln in text.splitlines()]
        outs = [ln for ln in lines if ln]
        log.info(
            f"✨ [RAG] MQE 扩展完成: query='{_query_preview(query)}', requested={n}, "
            f"generated={outs[:n]}, elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return outs[:n] or [query]
    except Exception as e:
        log.warn(f"✨ [RAG] mqe failed, using original query: query='{_query_preview(query)}', error={e}")
        return [query]


def _prompt_hyde(query: str) -> Optional[str]:
    try:
        t0 = time.time()
        llm = JosieLLM()
        prompt = [
            {"role": "system",
             "content": "根据用户问题，先写一段可能的答案性段落，用于向量检索的查询文档（不要分析过程）。"},
            {"role": "user", "content": f"问题：{query}\n请直接写一段中等长度、客观、包含关键术语的段落。"}
        ]
        text = clean_llm_resp(llm.invoke(prompt))

        log.info(
            f"🪞 [RAG] HYDE 扩展完成: query='{_query_preview(query)}', chars={len(text or '')}, "
            f"generated={text}, elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return text
    except Exception as e:
        log.warn(f"🪞 [RAG] hyde failed, continuing without hypothetical answer: query='{_query_preview(query)}', error={e}")
        return None

def clean_llm_resp(text: str) -> Optional[str]:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text


def search_vectors_expanded(
    store=None,
    query: str = "",
    top_k: int = 8,
    rag_namespace: Optional[str] = None,
    only_rag_data: bool = True,
    score_threshold: Optional[float] = None,
    enable_mqe: bool = False,
    mqe_expansions: int = 2,
    enable_hyde: bool = False,
    candidate_pool_multiplier: int = 4,
) -> List[Dict]:
    """
    Search with query expansion using unified embedding and Qdrant.
    """
    if not query:
        log.warn("🔎 [RAG] advanced_search skipped: empty_query")
        return []

    # Create default store if not provided
    if store is None:
        store = _create_default_vector_store()

    # expansions
    expansions: List[str] = [query]

    if enable_mqe and mqe_expansions > 0:
        expansions.extend(_prompt_mqe(query, mqe_expansions))
    if enable_hyde:
        hyde_text = _prompt_hyde(query)
        if hyde_text:
            expansions.append(hyde_text)

    # unique and trim
    uniq: List[str] = []
    for e in expansions:
        if e and e not in uniq:
            uniq.append(e)
    expansions = uniq[: max(1, len(uniq))]

    # distribute pool per expansion
    pool = max(top_k * candidate_pool_multiplier, 20)
    per = max(1, pool // max(1, len(expansions)))

    # Build filter for RAG data
    where = {"memory_type": "rag_chunk"}
    if only_rag_data:
        where["is_rag_data"] = True
        where["data_source"] = "rag_pipeline"
    if rag_namespace:
        where["rag_namespace"] = rag_namespace

    # collect hits across expansions
    t0 = time.time()
    log.info(
        f"🔎 [RAG] advanced_search start: 原始查询='{_query_preview(query)}', 扩展查询={expansions}, "
        f"top_k={top_k}, pool={pool}, per_query={per}, threshold={score_threshold}, "
        f"namespace={rag_namespace or 'all'}"
    )
    agg: Dict[str, Dict] = {}
    for q in expansions:
        qv = embed_query(q)
        hits = store.search_similar(query_vector=qv, limit=per, score_threshold=score_threshold, where=where)
        log.debug(f"🔎 [RAG] advanced_search expansion done: query='{_query_preview(q)}', hits={len(hits)}")
        for h in hits:
            mid = h.get("metadata", {}).get("memory_id", h.get("id"))
            s = float(h.get("score", 0.0))
            if mid not in agg or s > float(agg[mid].get("score", 0.0)):
                agg[mid] = h
    # return top by score
    merged = list(agg.values())
    merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    results = merged[:top_k]
    log.info(
        f"🔎 [RAG] advanced_search done: raw_unique_hits={len(merged)}, returned={len(results)}, "
        f"elapsed_ms={int((time.time() - t0) * 1000)}"
    )
    return results


def _try_load_cross_encoder(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    if CrossEncoder is None:
        log.warn(f"🏆 [RAG] reranker unavailable: missing sentence-transformers, model={model_name}")
        return None
    try:
        log.debug(f"🏆 [RAG] reranker load start: model={model_name}")
        return CrossEncoder(model_name)
    except Exception as e:
        log.warn(f"🏆 [RAG] reranker unavailable: model={model_name}, error={e}")
        return None


def rerank_with_cross_encoder(query: str, items: List[Dict], model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                              top_k: int = 10) -> List[Dict]:
    ce = _try_load_cross_encoder(model_name)
    if ce is None or not items:
        log.debug(f"🏆 [RAG] rerank skipped: items={len(items)}, top_k={top_k}")
        return items[:top_k]
    pairs = [[query, it.get("content", "")] for it in items]
    try:
        t0 = time.time()
        scores = ce.predict(pairs)
        for it, s in zip(items, scores):
            it["rerank_score"] = float(s)
        items.sort(key=lambda x: x.get("rerank_score", x.get("score", 0.0)), reverse=True)
        results = items[:top_k]
        log.info(
            f"🏆 [RAG] rerank done: input={len(items)}, returned={len(results)}, "
            f"elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return results
    except Exception as e:
        log.warn(f"🏆 [RAG] rerank failed, returning vector order: items={len(items)}, error={e}")
        return items[:top_k]


def compute_graph_signals_from_pool(vector_hits: List[Dict], same_doc_weight: float = 1.0,
                                    proximity_weight: float = 1.0, proximity_window_chars: int = 1600) -> Dict[
    str, float]:
    """
    Compute graph signals with direct parameters instead of environment variables.
    """

    # group by doc
    by_doc: Dict[str, List[Dict]] = {}
    for h in vector_hits:
        meta = h.get("metadata", {})
        did = meta.get("doc_id")
        if not did:
            # fall back to memory_id grouping if doc missing
            did = meta.get("memory_id") or h.get("id")
        by_doc.setdefault(did, []).append(h)

    # same-doc density score
    doc_counts = {d: len(arr) for d, arr in by_doc.items()}
    max_count = max(doc_counts.values()) if doc_counts else 1

    # proximity score per hit within same doc
    graph_signal: Dict[str, float] = {}
    for did, arr in by_doc.items():
        arr.sort(key=lambda x: x.get("metadata", {}).get("start", 0))
        # precompute density
        density = doc_counts.get(did, 1) / max_count
        # proximity accumulation
        for i, h in enumerate(arr):
            mid = h.get("metadata", {}).get("memory_id", h.get("id"))
            pos_i = h.get("metadata", {}).get("start", 0)
            prox_acc = 0.0
            # look around neighbors within window
            # two-pointer expansion
            # left
            j = i - 1
            while j >= 0:
                pos_j = arr[j].get("metadata", {}).get("start", 0)
                dist = abs(pos_i - pos_j)
                if dist > proximity_window_chars:
                    break
                prox_acc += max(0.0, 1.0 - (dist / max(1.0, float(proximity_window_chars))))
                j -= 1
            # right
            j = i + 1
            while j < len(arr):
                pos_j = arr[j].get("metadata", {}).get("start", 0)
                dist = abs(pos_i - pos_j)
                if dist > proximity_window_chars:
                    break
                prox_acc += max(0.0, 1.0 - (dist / max(1.0, float(proximity_window_chars))))
                j += 1
            # combine
            score = same_doc_weight * density + proximity_weight * prox_acc
            graph_signal[mid] = graph_signal.get(mid, 0.0) + score

    # normalize to [0,1]
    if graph_signal:
        max_v = max(graph_signal.values())
        if max_v > 0:
            for k in list(graph_signal.keys()):
                graph_signal[k] = graph_signal[k] / max_v
    return graph_signal


def rank(vector_hits: List[Dict], graph_signals: Optional[Dict[str, float]] = None, w_vector: float = 0.7,
         w_graph: float = 0.3) -> List[Dict]:
    """
    Rank results with direct weight parameters instead of environment variables.
    """
    items: List[Dict] = []
    graph_signals = graph_signals or {}
    for h in vector_hits:
        mid = h.get("metadata", {}).get("memory_id", h.get("id"))
        g = float(graph_signals.get(mid, 0.0))
        v = float(h.get("score", 0.0))
        score = w_vector * v + w_graph * g
        items.append({
            "memory_id": mid,
            "score": score,
            "vector_score": v,
            "graph_score": g,
            "content": h.get("metadata", {}).get("content", ""),
            "metadata": h.get("metadata", {}),
        })
    items.sort(key=lambda x: x["score"], reverse=True)
    return items


def merge_snippets(ranked_items: List[Dict], max_chars: int = 1200) -> str:
    out: List[str] = []
    total = 0
    for it in ranked_items:
        text = it.get("content", "").strip()
        if not text:
            continue
        if total + len(text) > max_chars:
            remain = max_chars - total
            if remain <= 0:
                break
            out.append(text[:remain])
            total += remain
            break
        out.append(text)
        total += len(text)
    return "\n\n".join(out)


def expand_neighbors_from_pool(selected: List[Dict], pool: List[Dict], neighbors: int = 1, max_additions: int = 5) -> \
List[Dict]:
    if not selected or not pool or neighbors <= 0:
        return selected
    # index pool by doc_id and sort by start
    by_doc: Dict[str, List[Dict]] = {}
    for it in pool:
        meta = it.get("metadata", {})
        did = meta.get("doc_id")
        if not did:
            continue
        by_doc.setdefault(did, []).append(it)
    for did, arr in by_doc.items():
        arr.sort(key=lambda x: (x.get("metadata", {}).get("start", 0)))
    selected_ids = set(it.get("memory_id") for it in selected)
    additions: List[Dict] = []
    for it in selected:
        meta = it.get("metadata", {})
        did = meta.get("doc_id")
        if not did or did not in by_doc:
            continue
        arr = by_doc[did]
        # find index
        try:
            idx = next(i for i, x in enumerate(arr) if x.get("memory_id") == it.get("memory_id"))
        except StopIteration:
            continue
        for offset in range(1, neighbors + 1):
            for j in (idx - offset, idx + offset):
                if 0 <= j < len(arr):
                    cand = arr[j]
                    mid = cand.get("memory_id")
                    if mid not in selected_ids:
                        additions.append(cand)
                        selected_ids.add(mid)
                        if len(additions) >= max_additions:
                            break
            if len(additions) >= max_additions:
                break
        if len(additions) >= max_additions:
            break
    # keep relative order by score
    extended = list(selected) + additions
    extended.sort(key=lambda x: (x.get("rerank_score", x.get("score", 0.0))), reverse=True)
    return extended


def merge_snippets_grouped(ranked_items: List[Dict], max_chars: int = 1200, include_citations: bool = True) -> str:
    # Group by doc_id and aggregate doc score
    by_doc: Dict[str, List[Dict]] = {}
    doc_score: Dict[str, float] = {}
    for it in ranked_items:
        meta = it.get("metadata", {})
        did = meta.get("doc_id") or meta.get("source_path") or "unknown"
        by_doc.setdefault(did, []).append(it)
        doc_score[did] = doc_score.get(did, 0.0) + float(it.get("score", 0.0))
    # Sort docs by aggregate score
    ordered_docs = sorted(by_doc.keys(), key=lambda d: doc_score.get(d, 0.0), reverse=True)
    # Within doc, order by start offset to preserve context
    for d in ordered_docs:
        by_doc[d].sort(key=lambda x: (x.get("metadata", {}).get("start", 0)))
    out: List[str] = []
    citations: List[Dict] = []
    total = 0
    cite_index = 1
    for did in ordered_docs:
        parts = by_doc[did]
        for it in parts:
            text = (it.get("content", "") or "").strip()
            if not text:
                continue
            # add citation marker if enabled
            suffix = ""
            if include_citations:
                suffix = f" [{cite_index}]"
            need = len(text) + (len(suffix) if suffix else 0)
            if total + need > max_chars:
                remain = max_chars - total
                if remain <= 0:
                    break
                clipped = text[: max(0, remain - len(suffix))]
                if clipped:
                    out.append(clipped + suffix)
                    total += len(clipped) + len(suffix)
                    if include_citations:
                        m = it.get("metadata", {})
                        citations.append({
                            "index": cite_index,
                            "source_path": m.get("source_path"),
                            "doc_id": m.get("doc_id"),
                            "start": m.get("start"),
                            "end": m.get("end"),
                            "heading_path": m.get("heading_path"),
                        })
                        cite_index += 1
                break
            out.append(text + suffix)
            total += need
            if include_citations:
                m = it.get("metadata", {})
                citations.append({
                    "index": cite_index,
                    "source_path": m.get("source_path"),
                    "doc_id": m.get("doc_id"),
                    "start": m.get("start"),
                    "end": m.get("end"),
                    "heading_path": m.get("heading_path"),
                })
                cite_index += 1
        if total >= max_chars:
            break
    merged = "\n\n".join(out)
    if include_citations and citations:
        lines: List[str] = [merged, "", "References:"]
        for c in citations:
            loc = ""
            if c.get("start") is not None and c.get("end") is not None:
                loc = f" ({c['start']}-{c['end']})"
            hp = f" – {c['heading_path']}" if c.get("heading_path") else ""
            sp = c.get("source_path") or c.get("doc_id") or "source"
            lines.append(f"[{c['index']}] {sp}{loc}{hp}")
        return "\n".join(lines)
    return merged


def compress_ranked_items(ranked_items: List[Dict], enable_compression: bool = True, max_per_doc: int = 2,
                          join_gap: int = 200) -> List[Dict]:
    """
    Compress ranked items with direct parameters instead of environment variables.
    """
    if not enable_compression:
        return ranked_items
    by_doc_count: Dict[str, int] = {}
    last_by_doc: Dict[str, Dict] = {}
    new_items: List[Dict] = []
    for it in ranked_items:
        meta = it.get("metadata", {})
        did = meta.get("doc_id") or meta.get("source_path") or "unknown"
        start = int(meta.get("start") or 0)
        end = int(meta.get("end") or (start + len(it.get("content", "") or "")))
        if did not in last_by_doc:
            last_by_doc[did] = it
            by_doc_count[did] = 1
            new_items.append(it)
            continue
        last = last_by_doc[did]
        lmeta = last.get("metadata", {})
        lstart = int(lmeta.get("start") or 0)
        lend = int(lmeta.get("end") or (lstart + len(last.get("content", "") or "")))
        if start - lend <= join_gap and start >= lstart:
            # merge into last
            merged_text = (last.get("content", "") or "").strip()
            add_text = (it.get("content", "") or "").strip()
            if add_text:
                if merged_text:
                    merged_text = merged_text + "\n\n" + add_text
                else:
                    merged_text = add_text
                last["content"] = merged_text
                lmeta["end"] = max(lend, end)
                # keep the higher score
                try:
                    last["score"] = max(float(last.get("score", 0.0)), float(it.get("score", 0.0)))
                except Exception:
                    pass
            last_by_doc[did] = last
        else:
            cnt = by_doc_count.get(did, 0)
            if cnt >= max_per_doc:
                continue
            new_items.append(it)
            last_by_doc[did] = it
            by_doc_count[did] = cnt + 1
    return new_items


def tldr_summarize(text: str, bullets: int = 3) -> Optional[str]:
    try:
        if not text or len(text.strip()) == 0:
            return None
        llm = JosieLLM()
        prompt = [
            {"role": "system", "content": "请将以下内容概括为简洁的要点列表（最多3-5条），用中文，避免重复，突出关键信息。"},
            {"role": "user", "content": f"请用 {max(1, min(5, int(bullets)))} 条要点总结：\n\n{text}"},
        ]
        out = llm.invoke(prompt)
        return out
    except Exception:
        return None


# ==================
# High-level RAG Pipeline API
# ==================

def create_rag_pipeline(
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "rag_knowledge_base",
        rag_namespace: str = "default"
) -> Dict[str, Any]:
    """
    Create a complete RAG pipeline with Qdrant and unified embedding.

    Returns:
        Dict containing store, namespace, and helper functions
    """
    dimension = get_dimension(384)
    log.debug(
        f"⚙️ [RAG] pipeline create start: collection={collection_name}, "
        f"namespace={rag_namespace}, dimension={dimension}"
    )

    store = QdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name,
        vector_size=dimension,
        distance="cosine"
    )
    log.success(f"⚙️ [RAG] pipeline create done: collection={collection_name}, namespace={rag_namespace}")

    def add_documents(file_paths: List[str], chunk_size: int = 800, chunk_overlap: int = 100):
        """Add documents to RAG pipeline"""
        t0 = time.time()
        log.debug(
            f"📥 [RAG] add_documents start: file_num={len(file_paths)}, namespace={rag_namespace}, "
            f"chunk_size={chunk_size}, overlap={chunk_overlap}"
        )
        chunks = load_and_chunk_texts(
            paths=file_paths,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            namespace=rag_namespace,
            source_label="rag"
        )
        index_chunks(
            store=store,
            chunks=chunks,
            rag_namespace=rag_namespace
        )
        log.info(
            f"📥 [RAG] add_documents done: files={len(file_paths)}, chunks={len(chunks)}, "
            f"namespace={rag_namespace}, elapsed_ms={int((time.time() - t0) * 1000)}"
        )
        return len(chunks)

    def search(query: str, top_k: int = 8, score_threshold: Optional[float] = None):
        """Search RAG knowledge base"""
        log.info(
            f"🔎 [RAG] pipeline search: query='{_query_preview(query)}', top_k={top_k}, "
            f"threshold={score_threshold}, namespace={rag_namespace}"
        )
        return search_vectors(
            store=store,
            query=query,
            top_k=top_k,
            rag_namespace=rag_namespace,
            score_threshold=score_threshold
        )

    def search_advanced(
            query: str,
            top_k: int = 8,
            enable_mqe: bool = False,
            enable_hyde: bool = False,
            score_threshold: Optional[float] = None
    ):
        """Advanced search with query expansion"""
        log.info(
            f"🔎 [RAG] pipeline advanced_search: query='{_query_preview(query)}', top_k={top_k}, "
            f"mqe={enable_mqe}, hyde={enable_hyde}, threshold={score_threshold}, "
            f"namespace={rag_namespace}"
        )
        return search_vectors_expanded(
            store=store,
            query=query,
            top_k=top_k,
            rag_namespace=rag_namespace,
            enable_mqe=enable_mqe,
            enable_hyde=enable_hyde,
            score_threshold=score_threshold
        )

    def get_stats():
        """Get pipeline statistics"""
        log.info(f"📊 [RAG] stats start: namespace={rag_namespace}, collection={collection_name}")
        stats = store.get_collection_stats()
        log.info(f"📊 [RAG] stats done: namespace={rag_namespace}, keys={list(stats.keys())}")
        return stats

    return {
        "store": store,
        "namespace": rag_namespace,
        "add_documents": add_documents,
        "search": search,
        "search_advanced": search_advanced,
        "get_stats": get_stats
    }
