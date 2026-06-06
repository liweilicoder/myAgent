# EpisodicMemory 交互流程分析

基于现有信息，我理解需求是：把 `EpisodicMemory` 的真实交互路径讲清楚，包括 `self` 上各组件之间怎么协作、它和 storage 层怎么交互、每个 public/private 方法的调用路径是什么，并用 Mermaid 流程图落到同目录文档里。

## 核心判断

值得分析。原因很简单：`EpisodicMemory` 表面是一个记忆类型，实际同时维护内存缓存、SQLite 权威库、Qdrant 向量索引、外部 `storage_backend` 四套状态。这里最容易出错的不是算法，而是数据所有权不清。

关键洞察：

- 数据结构：`Episode` 是运行期缓存记录；`MemoryItem` 是对外协议；SQLite `memories` 表是当前代码注释里的“权威存储”；Qdrant 只是语义检索索引。
- 复杂度：`self.storage` 不是主存储，只被 `_persist_episode()` 和 `_remove_from_storage()` 两个私有方法使用，而主流程根本不调用它。
- 风险点：`has_memory()`、`get_all()`、`get_stats()` 依赖 `self.episodes`，重启后如果不从 SQLite 回灌内存缓存，这些方法就会和权威库脱节。

## 组件关系

```mermaid
flowchart TB
    Caller["调用方 / MemoryManager"] --> EM["EpisodicMemory"]

    subgraph Self["EpisodicMemory self 组件"]
        Config["self.config<br/>MemoryConfig"]
        ExtStorage["self.storage<br/>外部 storage_backend，可选"]
        Episodes["self.episodes<br/>List[Episode] 运行期缓存"]
        Sessions["self.sessions<br/>session_id -> episode_ids"]
        PatternCache["self.patterns_cache<br/>模式识别缓存"]
        LastAnalysis["self.last_pattern_analysis"]
        DocStore["self.doc_store<br/>SQLiteDocumentStore"]
        Embedder["self.embedder<br/>全局文本嵌入模型"]
        VectorStore["self.vector_store<br/>QdrantVectorStore"]
    end

    EM --> Config
    EM --> ExtStorage
    EM --> Episodes
    EM --> Sessions
    EM --> PatternCache
    EM --> LastAnalysis
    EM --> DocStore
    EM --> Embedder
    EM --> VectorStore

    DocStore --> SQLite["SQLite memory.db<br/>users / memories / concepts / relationships"]
    Embedder --> Provider["DashScope / Local Transformer / TF-IDF"]
    VectorStore --> Qdrant["Qdrant collection<br/>payload: memory_id/user_id/memory_type/session_id/content"]
    ExtStorage -.只被私有方法调用.-> External["外部 add_memory/delete_memory 后端"]
```

## 数据所有权

`add()` 写入顺序是先内存，再 SQLite，再 Qdrant。注释说 SQLite 是权威库，这个判断基本合理，但代码没有在初始化时从 SQLite 恢复 `self.episodes`。所以运行时看起来是三份数据：

```mermaid
flowchart LR
    MI["MemoryItem<br/>对外输入/输出协议"] --> EP["Episode<br/>内存缓存"]
    MI --> DB["SQLite memories<br/>权威记录"]
    MI --> VEC["Qdrant point<br/>语义索引"]

    EP -->|"has_memory / get_all / get_stats / timeline / patterns"| RuntimeRead["运行期读取"]
    DB -->|"retrieve 完整记录 / update / delete / stats"| DurableRead["持久层读取"]
    VEC -->|"retrieve 相似候选"| SemanticRead["语义召回"]
```

坏味道在这里：权威库和缓存之间没有恢复、同步校验、事务边界。SQLite 写失败时，内存已经被追加；Qdrant 写失败会被吞掉。这不是灾难，但别假装它强一致。

## 初始化流程

```mermaid
flowchart TD
    A["EpisodicMemory(config, storage_backend)"] --> B["BaseMemory.__init__"]
    B --> C["设置 self.config"]
    B --> D["设置 self.storage"]
    B --> E["计算 self.memory_type = episodic"]

    E --> F["初始化 self.episodes = []"]
    F --> G["初始化 self.sessions = {}"]
    G --> H["初始化 patterns_cache / last_pattern_analysis"]

    H --> I["读取 config.storage_path<br/>默认 ./memory_data"]
    I --> J["创建目录"]
    J --> K["构造 memory.db 路径"]
    K --> L["SQLiteDocumentStore(db_path)"]
    L --> M["同路径单例复用或创建"]
    M --> N["线程本地 sqlite connection"]
    N --> O["创建 users / memories / concepts / 关联表和索引"]

    O --> P["get_text_embedder()"]
    P --> Q["全局嵌入模型单例<br/>dashscope -> local -> tfidf fallback"]
    Q --> R["get_database_config()"]
    R --> S["读取 Qdrant 环境配置"]
    S --> T["vector_size = get_dimension()"]
    T --> U["QdrantConnectionManager.get_instance"]
    U --> V["同 url + collection 单例复用或创建"]
    V --> W["QdrantVectorStore 初始化 client"]
    W --> X["ensure collection"]
    X --> Y["ensure payload indexes"]
```

## Storage 层交互

### SQLiteDocumentStore

```mermaid
flowchart TB
    EM["EpisodicMemory"] --> AddDB["doc_store.add_memory"]
    EM --> GetDB["doc_store.get_memory"]
    EM --> SearchDB["doc_store.search_memories"]
    EM --> UpdateDB["doc_store.update_memory"]
    EM --> DeleteDB["doc_store.delete_memory"]
    EM --> StatsDB["doc_store.get_database_stats"]

    AddDB --> Users["INSERT OR IGNORE users"]
    AddDB --> UpsertMem["INSERT OR REPLACE memories"]
    GetDB --> SelectOne["SELECT memories WHERE id = ?"]
    SearchDB --> SelectMany["SELECT memories<br/>WHERE user/type/time/importance<br/>ORDER BY importance DESC, timestamp DESC"]
    UpdateDB --> UpdateMem["UPDATE memories SET changed fields"]
    DeleteDB --> DelMem["DELETE FROM memories WHERE id = ?"]
    StatsDB --> CountTables["COUNT users/memories/concepts/..."]
```

### QdrantVectorStore

```mermaid
flowchart TB
    EM["EpisodicMemory"] --> Encode["embedder.encode(text/query)"]
    Encode --> Vec["vector list"]
    Vec --> AddVec["vector_store.add_vectors"]
    Vec --> SearchVec["vector_store.search_similar"]

    AddVec --> Validate["检查向量维度"]
    Validate --> Payload["补 timestamp/added_at payload"]
    Payload --> SafeId["point id 必须是 int 或 UUID<br/>否则换成随机 UUID"]
    SafeId --> Upsert["client.upsert(wait=True)"]

    SearchVec --> Filter["构造 payload filter<br/>memory_type/user_id"]
    Filter --> Search["client.search(with_payload=True)"]
    Search --> Hits["返回 id/score/metadata"]

    EM --> DeleteVec["vector_store.delete_memories(memory_ids)"]
    DeleteVec --> DeleteByPayload["按 payload.memory_id 删除<br/>不依赖 point id"]
```

这里的设计有个正确选择：删除向量按 payload `memory_id` 做，不依赖 Qdrant point id。因为写入时非 UUID 字符串会被换成随机 UUID，靠 point id 删除会破坏用户空间。

## 方法交互路径

### add(memory_item)

```mermaid
flowchart TD
    A["add(memory_item)"] --> B["从 metadata 提取 session_id/context/outcome/participants/tags"]
    B --> C["构造 Episode"]
    C --> D["append 到 self.episodes"]
    D --> E{"session_id 是否存在于 self.sessions"}
    E -->|否| F["self.sessions[session_id] = []"]
    E -->|是| G["继续"]
    F --> H["追加 episode_id 到 session 列表"]
    G --> H

    H --> I["doc_store.add_memory<br/>写 SQLite 权威库"]
    I --> J["embedder.encode(content)"]
    J --> K["embedding.tolist 如果需要"]
    K --> L["vector_store.add_vectors<br/>写 Qdrant 语义索引"]
    L --> M["返回 memory_item.id"]
    J -.异常吞掉.-> M
    L -.异常吞掉.-> M
```

风险：

- SQLite 写入不在 `try` 里，失败会抛出；但失败发生前内存缓存已经追加，状态会脏。
- Qdrant 写入失败被吞掉，检索会失去语义召回，但 SQLite 记录仍存在。

### retrieve(query, limit, **kwargs)

```mermaid
flowchart TD
    A["retrieve(query, limit, user_id, session_id, time_range, min_importance)"] --> B{"是否有 time_range 或 min_importance"}
    B -->|是| C["doc_store.search_memories<br/>取结构化候选 candidate_ids"]
    B -->|否| D["candidate_ids = None"]
    C --> E["embedder.encode(query)"]
    D --> E
    E --> F["vector_store.search_similar<br/>where: memory_type=episodic, user_id?"]
    E -.异常.-> G["hits = []"]
    F --> H["遍历 hits"]
    G --> Z{"results 是否为空"}

    H --> I{"memory_id 缺失或重复"}
    I -->|是| H
    I -->|否| J["查 self.episodes 里的同 ID episode"]
    J --> K{"episode.context.forgotten 为 true"}
    K -->|是| H
    K -->|否| L{"candidate_ids 存在且 mem_id 不在其中"}
    L -->|是| H
    L -->|否| M{"session_id 存在且 payload session 不匹配"}
    M -->|是| H
    M -->|否| N["doc_store.get_memory(mem_id)<br/>读取完整权威记录"]
    N --> O{"doc 是否存在"}
    O -->|否| H
    O -->|是| P["计算 vec_score / recency_score / importance_weight"]
    P --> Q["组装 MemoryItem<br/>metadata 带 relevance_score/vector_score/recency_score"]
    Q --> R["加入 results"]
    R --> H

    H --> Z
    Z -->|否| S["按 combined 降序排序"]
    Z -->|是| T["回退：_filter_episodes 走内存缓存"]
    T --> U["query_lower in ep.content.lower()"]
    U --> V["计算关键词得分 + 近因 + 重要性权重"]
    V --> W["组装 MemoryItem"]
    W --> S
    S --> X["返回前 limit 条 MemoryItem"]
```

风险：

- 如果 Qdrant 不可用，只回退内存缓存，不回退 SQLite 全文/结构化搜索。重启后缓存空，SQLite 有数据也检索不到。
- `forgotten` 检查还留着软删除痕迹，但 `forget()` 已经是硬删除。这个分支是历史包袱。

### update(memory_id, content, importance, metadata)

```mermaid
flowchart TD
    A["update(memory_id, content, importance, metadata)"] --> B["遍历 self.episodes"]
    B --> C{"找到 episode"}
    C -->|是| D["更新 episode.content / importance / context / outcome"]
    C -->|否| E["updated = False"]
    D --> F["updated = True"]
    E --> G["doc_store.update_memory"]
    F --> G
    G --> H{"content 是否变更"}
    H -->|否| I["返回 updated or doc_updated"]
    H -->|是| J["embedder.encode(content)"]
    J --> K["doc_store.get_memory(memory_id)<br/>同步 payload"]
    K --> L["vector_store.add_vectors<br/>upsert 新向量"]
    L --> I
    J -.异常吞掉.-> I
    L -.异常吞掉.-> I
```

风险：

- 只更新 `importance` 时不会同步 Qdrant payload 里的 `importance`，向量索引 metadata 可能变旧。
- SQLite 的 `properties` 被整体替换为 `metadata`，但内存里只合并 `metadata.context` 和 `outcome`。两边语义不一致。

### remove(memory_id)

```mermaid
flowchart TD
    A["remove(memory_id)"] --> B["遍历 self.episodes"]
    B --> C{"找到 episode"}
    C -->|是| D["pop episode"]
    D --> E["从 self.sessions[session_id] 删除 memory_id"]
    E --> F{"session 列表是否为空"}
    F -->|是| G["删除 session key"]
    F -->|否| H["保留 session key"]
    C -->|否| I["removed = False"]
    G --> J["doc_store.delete_memory(memory_id)"]
    H --> J
    I --> J
    J --> K["vector_store.delete_memories([memory_id])"]
    K --> L["返回 removed or doc_deleted"]
    K -.异常吞掉.-> L
```

### clear()

```mermaid
flowchart TD
    A["clear()"] --> B["self.episodes.clear"]
    B --> C["self.sessions.clear"]
    C --> D["self.patterns_cache.clear"]
    D --> E["doc_store.search_memories(memory_type=episodic, limit=10000)"]
    E --> F["逐个 doc_store.delete_memory"]
    F --> G{"ids 是否为空"}
    G -->|否| H["vector_store.delete_memories(ids)"]
    G -->|是| I["结束"]
    H --> I
    H -.异常吞掉.-> I
```

风险：先清内存，再清 SQLite。如果 SQLite 删除失败，内存和权威库立刻分裂。

### forget(strategy, threshold, max_age_days)

```mermaid
flowchart TD
    A["forget(strategy, threshold, max_age_days)"] --> B["遍历 self.episodes"]
    B --> C{"strategy"}
    C -->|"importance_based"| D["episode.importance < threshold"]
    C -->|"time_based"| E["episode.timestamp < now - max_age_days"]
    C -->|"capacity_based"| F["len(episodes) > config.max_capacity<br/>删除最低重要性 excess_count"]
    C -->|"未知"| G["不删除"]
    D --> H{"should_forget"}
    E --> H
    F --> H
    G --> B
    H -->|是| I["加入 to_remove"]
    H -->|否| B
    I --> B
    B --> J["遍历 to_remove"]
    J --> K["remove(episode_id)<br/>硬删除内存 + SQLite + Qdrant"]
    K --> L["forgotten_count++"]
    L --> J
    J --> M["返回 forgotten_count"]
```

### has_memory(memory_id)

```mermaid
flowchart TD
    A["has_memory(memory_id)"] --> B["只扫描 self.episodes"]
    B --> C["返回是否存在 episode_id"]
```

风险：它不查 SQLite。重启后没有回灌缓存，`has_memory()` 会把持久层存在的记忆判断为不存在。

### get_all()

```mermaid
flowchart TD
    A["get_all()"] --> B["遍历 self.episodes"]
    B --> C["Episode -> MemoryItem"]
    C --> D["metadata = episode.metadata"]
    D --> E["返回列表"]
```

致命问题：`Episode` 没有 `metadata` 字段，这个方法运行到第一条记录就会 `AttributeError`。这不是风格问题，是直接坏。

### get_stats()

```mermaid
flowchart TD
    A["get_stats()"] --> B["active_episodes = self.episodes"]
    B --> C["doc_store.get_database_stats()"]
    C --> D["vector_store.get_collection_stats()"]
    D -.异常.-> E["vs_stats = {'store_type': 'qdrant'}"]
    D --> F["组装 count/sessions/avg_importance/time_span"]
    E --> F
    F --> G["document_store 只保留 *_count/store_type/db_path"]
    G --> H["返回 stats"]
```

这里统计的是“缓存状态 + 持久层统计”的混合物。`count` 来自缓存，`document_store.memories_count` 来自 SQLite。两者不一致时没有任何告警。

### get_session_episodes(session_id)

```mermaid
flowchart TD
    A["get_session_episodes(session_id)"] --> B{"session_id 是否在 self.sessions"}
    B -->|否| C["返回 []"]
    B -->|是| D["取 episode_ids"]
    D --> E["扫描 self.episodes，返回 ID 命中的 Episode"]
```

### find_patterns(user_id, min_frequency)

```mermaid
flowchart TD
    A["find_patterns(user_id, min_frequency)"] --> B["cache_key = user_id_min_frequency"]
    B --> C{"缓存命中且 last_pattern_analysis 未超过 1 小时"}
    C -->|是| D["返回 patterns_cache[cache_key]"]
    C -->|否| E["按 user_id 过滤 self.episodes"]
    E --> F["按 content.lower().split() 统计长度 > 3 的词"]
    F --> G["按 context key:value 统计上下文模式"]
    G --> H["筛选 frequency >= min_frequency"]
    H --> I["confidence = frequency / len(episodes)"]
    I --> J["按 frequency 降序"]
    J --> K["写入 patterns_cache 和 last_pattern_analysis"]
    K --> L["返回 patterns"]
```

致命问题：`(datetime.now() - self.last_pattern_analysis).hours` 不存在，`timedelta` 没有 `hours` 属性。缓存命中路径会崩。应该用 `total_seconds() < 3600`。

### get_timeline(user_id, limit)

```mermaid
flowchart TD
    A["get_timeline(user_id, limit)"] --> B["按 user_id 过滤 self.episodes"]
    B --> C["按 timestamp 倒序排序"]
    C --> D["截取前 limit 条"]
    D --> E["输出 episode_id/timestamp/content/session_id/importance/outcome"]
```

### _filter_episodes(user_id, session_id, time_range)

```mermaid
flowchart TD
    A["_filter_episodes(...)"] --> B["filtered = self.episodes"]
    B --> C{"user_id?"}
    C -->|是| D["过滤 user_id"]
    C -->|否| E["跳过"]
    D --> F{"session_id?"}
    E --> F
    F -->|是| G["过滤 session_id"]
    F -->|否| H["跳过"]
    G --> I{"time_range?"}
    H --> I
    I -->|是| J["过滤 start_time <= timestamp <= end_time"]
    I -->|否| K["返回 filtered"]
    J --> K
```

### _persist_episode(episode) 与 _remove_from_storage(memory_id)

```mermaid
flowchart TD
    A["_persist_episode(episode)"] --> B{"self.storage 存在且有 add_memory"}
    B -->|是| C["self.storage.add_memory(...)"]
    B -->|否| D["什么也不做"]

    E["_remove_from_storage(memory_id)"] --> F{"self.storage 存在且有 delete_memory"}
    F -->|是| G["self.storage.delete_memory(memory_id)"]
    F -->|否| H["什么也不做"]
```

这两个方法是“外部 storage_backend 适配钩子”，但 `add()`、`remove()`、`clear()`、`forget()` 都没有调用它们。也就是说，当前主流程里的 storage 不是 `self.storage`，而是 `self.doc_store` 和 `self.vector_store`。

## 与 MemoryManager 的入口关系

```mermaid
flowchart TD
    MM["MemoryManager"] --> Init["__init__ 启用 episodic"]
    Init --> EM["EpisodicMemory(config)"]

    MMAdd["MemoryManager.add_memory"] --> Classify["_classify_memory_type"]
    Classify -->|"episodic"| MakeItem["构造 MemoryItem"]
    MakeItem --> EMAdd["EpisodicMemory.add"]

    MMRetrieve["MemoryManager.retrieve_memories"] --> EMRetrieve["EpisodicMemory.retrieve"]
    MMUpdate["MemoryManager.update_memory"] --> Has["EpisodicMemory.has_memory"]
    Has -->|"true"| EMUpdate["EpisodicMemory.update"]
    MMRemove["MemoryManager.remove_memory"] --> Has2["EpisodicMemory.has_memory"]
    Has2 -->|"true"| EMRemove["EpisodicMemory.remove"]
    MMForget["MemoryManager.forget_memories"] --> EMForget["EpisodicMemory.forget"]
    MMStats["MemoryManager.get_memory_stats"] --> EMStats["EpisodicMemory.get_stats"]
```

这里 `MemoryManager.update_memory()` 和 `remove_memory()` 依赖 `has_memory()` 找类型，而 `has_memory()` 只看内存缓存。这意味着持久层里存在但缓存里没有的 episodic 记忆，Manager 无法更新或删除。

## 完整主流程总图

```mermaid
flowchart TB
    subgraph Entry["入口"]
        AddEntry["add"]
        RetrieveEntry["retrieve"]
        UpdateEntry["update"]
        RemoveEntry["remove"]
        ClearEntry["clear"]
        ForgetEntry["forget"]
        ReadEntry["get_all / get_stats / timeline / patterns / session"]
    end

    subgraph Runtime["运行期缓存"]
        Episodes["self.episodes"]
        Sessions["self.sessions"]
        PatternCache["self.patterns_cache"]
    end

    subgraph Durable["持久层"]
        SQLite["SQLiteDocumentStore<br/>memory.db"]
        Qdrant["QdrantVectorStore<br/>semantic index"]
        Embedder["Text Embedder"]
        ExternalStorage["self.storage<br/>仅私有钩子"]
    end

    AddEntry --> Episodes
    AddEntry --> Sessions
    AddEntry --> SQLite
    AddEntry --> Embedder
    Embedder --> Qdrant

    RetrieveEntry --> SQLite
    RetrieveEntry --> Embedder
    RetrieveEntry --> Qdrant
    RetrieveEntry --> Episodes

    UpdateEntry --> Episodes
    UpdateEntry --> SQLite
    UpdateEntry --> Embedder
    UpdateEntry --> Qdrant

    RemoveEntry --> Episodes
    RemoveEntry --> Sessions
    RemoveEntry --> SQLite
    RemoveEntry --> Qdrant

    ClearEntry --> Episodes
    ClearEntry --> Sessions
    ClearEntry --> PatternCache
    ClearEntry --> SQLite
    ClearEntry --> Qdrant

    ForgetEntry --> Episodes
    ForgetEntry --> RemoveEntry

    ReadEntry --> Episodes
    ReadEntry --> Sessions
    ReadEntry --> PatternCache
    ReadEntry --> SQLite
    ReadEntry --> Qdrant

    ExternalHook["_persist_episode / _remove_from_storage"] -.手动调用才生效.-> ExternalStorage
```

## 品味评分

凑合，但偏脆。

不是因为用了 SQLite + Qdrant，这个选择没问题。问题是边界情况太多：缓存、权威库、索引、外部 storage 钩子各自为政，没有统一的数据生命周期。好代码应该让特殊情况消失，而不是到处 `try/except/pass`。

## 致命问题

- `get_all()` 访问不存在的 `episode.metadata`，有数据时必崩。
- `find_patterns()` 的缓存命中路径访问不存在的 `timedelta.hours`，命中缓存时必崩。
- `has_memory()` 只查内存缓存，导致重启后持久化记忆对 `MemoryManager.update_memory/remove_memory` 不可见。
- `self.storage` 名字误导。真正主存储是 `self.doc_store`，外部 `storage_backend` 只是死钩子。

## 改进方向

1. 第一步简化数据结构：明确 SQLite 是唯一权威，`self.episodes` 是可重建缓存。
2. 初始化时从 SQLite 回灌 episodic 缓存，或者删掉依赖缓存判断存在性的逻辑。
3. 把 `add/update/remove/clear` 的状态变更顺序统一成“先权威库，后缓存，最后索引”。
4. 不要吞掉 Qdrant 异常后完全无记录，至少写日志；索引失败不是业务失败，但必须可观察。
5. 修掉 `get_all()` 和 `find_patterns()` 两个直接运行时错误。
