"""
Transformer 模型实现
基于 Vaswani et al. "Attention Is All You Need" 论文
实现编码器-解码器架构
"""

# ============================================================
# 依赖导入
# ============================================================

import torch                    # PyTorch 张量运算框架
import torch.nn as nn           # PyTorch 神经网络模块
import math                     # 数学运算（用于注意力缩放）
import copy                     # 深拷贝工具


# ============================================================
# 多头注意力机制 (Multi-Head Attention)
# ============================================================

class MultiHeadAttention(nn.Module):
    """
    多头注意力机制模块

    核心思想：将 Q(查询)、K(键)、V(值) 分别投影到多个子空间，
    在每个子空间独立计算注意力，最后拼接输出。

    公式：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k))V
    多头形式：MultiHead(Q,K,V) = Concat(head_1,...,head_h)W^O
    """

    def __init__(self, d_model, num_heads):
        """
        初始化多头注意力层

        参数:
            d_model: 模型的隐藏维度（词嵌入维度）
            num_heads: 注意力头数量
        """
        super(MultiHeadAttention, self).__init__()  # 调用父类 nn.Module 的初始化方法
        # 断言确保 d_model 能被 num_heads 整除，这样才能公平地分割为多个头
        assert d_model % num_heads == 0, "d_model 必须能被 num_heads 整除"

        # 保存各维度参数
        self.d_model = d_model           # 模型隐藏维度，如 512
        self.num_heads = num_heads      # 注意力头数量，如 8
        self.d_k = d_model // num_heads # 每个头的维度，如 512/8=64

        # 定义四个线性变换层，用于将输入投影到 Q、K、V 空间以及输出
        self.W_q = nn.Linear(d_model, d_model)  # Q 的线性变换
        self.W_k = nn.Linear(d_model, d_model)  # K 的线性变换
        self.W_v = nn.Linear(d_model, d_model)  # V 的线性变换
        self.W_o = nn.Linear(d_model, d_model)  # 输出线性变换

    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        """
        缩放点积注意力计算

        公式：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k))V

        参数:
            Q: 查询张量，形状 (batch_size, num_heads, seq_len, d_k)
            K: 键张量，形状 (batch_size, num_heads, seq_len, d_k)
            V: 值张量，形状 (batch_size, num_heads, seq_len, d_k)
            mask: 可选掩码张量，用于遮盖某些位置

        返回:
            加权求和后的输出，形状 (batch_size, num_heads, seq_len, d_k)
        """
        # 1. 计算注意力得分：QK^T，除以 sqrt(d_k) 用于缩放防止梯度消失
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)

        # 2. 如果提供了掩码，应用掩码：将需要遮盖的位置（mask==0）设为很小的负数
        #    这样 softmax 后这些位置的权重会接近 0
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)

        # 3. 对注意力得分进行 softmax 操作，得到注意力权重（概率分布）
        attn_probs = torch.softmax(attn_scores, dim=-1)

        # 4. 用注意力权重对 V 进行加权求和
        output = torch.matmul(attn_probs, V)
        return output

    def split_heads(self, x):
        """
        将输入张量分割成多个注意力头

        输入形状: (batch_size, seq_length, d_model)
        输出形状: (batch_size, num_heads, seq_length, d_k)

        参数:
            x: 输入张量
        返回:
            分割多头后的张量
        """
        batch_size, seq_length, d_model = x.size()  # 获取批次大小、序列长度、模型维度
        # view 用于重塑张量，transpose(1,2) 用于交换第1和第2维
        # 最终形状：(batch_size, num_heads, seq_length, d_k)
        return x.view(batch_size, seq_length, self.num_heads, self.d_k).transpose(1, 2)

    def combine_heads(self, x):
        """
        将多个注意力头的输出合并回原始维度

        输入形状: (batch_size, num_heads, seq_length, d_k)
        输出形状: (batch_size, seq_length, d_model)

        参数:
            x: 多头输出张量
        返回:
            合并后的张量
        """
        batch_size, num_heads, seq_length, d_k = x.size()  # 获取各维度大小
        # transpose(1,2) 恢复为 (batch_size, seq_length, num_heads, d_k)
        # contiguous() 确保张量在内存中是连续的
        # view() 将其重塑为 (batch_size, seq_length, d_model)
        return x.transpose(1, 2).contiguous().view(batch_size, seq_length, self.d_model)

    def forward(self, Q, K, V, mask=None):
        """
        多头注意力前向传播

        参数:
            Q: 查询张量
            K: 键张量
            V: 值张量
            mask: 可选掩码

        返回:
            注意力加权输出
        """
        # 1. 对 Q、K、V 分别进行线性变换，然后分割成多个头
        Q = self.split_heads(self.W_q(Q))
        K = self.split_heads(self.W_k(K))
        V = self.split_heads(self.W_v(V))

        # 2. 计算缩放点积注意力
        attn_output = self.scaled_dot_product_attention(Q, K, V, mask)

        # 3. 合并多头输出，通过最终的线性变换层
        output = self.W_o(self.combine_heads(attn_output))
        return output


# ============================================================
# 位置前馈网络 (Position-wise Feed-Forward Network)
# ============================================================

class PositionWiseFeedForward(nn.Module):
    """
    位置前馈网络模块

    两层全连接网络，对序列中每个位置独立应用相同的变换
    公式：FFN(x) = max(0, xW_1 + b_1)W_2 + b_2

    参数:
        d_model: 输入/输出维度
        d_ff: 中间层维度（通常为 d_model 的 4 倍）
        dropout: Dropout 比率
    """

    def __init__(self, d_model, d_ff, dropout=0.1):
        """初始化前馈网络"""
        super(PositionWiseFeedForward, self).__init__()  # 调用父类初始化

        # 第一层线性变换：d_model -> d_ff
        self.linear1 = nn.Linear(d_model, d_ff)
        self.dropout = nn.Dropout(dropout)  # Dropout 层
        # 第二层线性变换：d_ff -> d_model
        self.linear2 = nn.Linear(d_ff, d_model)
        self.relu = nn.ReLU()  # ReLU 激活函数

    def forward(self, x):
        """
        前馈网络前向传播

        参数:
            x: 输入张量，形状 (batch_size, seq_len, d_model)

        返回:
            输出张量，形状 (batch_size, seq_len, d_model)
        """
        # 第一层线性变换 + ReLU 激活
        x = self.linear1(x)
        x = self.relu(x)
        # Dropout 正则化
        x = self.dropout(x)
        # 第二层线性变换
        x = self.linear2(x)
        return x


# ============================================================
# 位置编码 (Positional Encoding)
# ============================================================

class PositionalEncoding(nn.Module):
    """
    位置编码模块

    由于 Transformer 没有循环结构，需要显式注入位置信息。
    使用正弦和余弦函数编码位置：
        PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    参数:
        d_model: 词嵌入维度
        dropout: Dropout 比率
        max_len: 最大序列长度
    """

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        """初始化位置编码"""
        super().__init__()  # 调用父类初始化
        self.dropout = nn.Dropout(p=dropout)  # Dropout 层

        # 创建位置索引：[0, 1, 2, ..., max_len-1]，形状 (max_len, 1)
        position = torch.arange(max_len).unsqueeze(1)

        # 计算除数项：10000^(2i/d_model) 的倒数用于缩放
        # torch.arange(0, d_model, 2) 产生 [0, 2, 4, ..., d_model-2]
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))

        # 初始化位置编码矩阵，形状 (max_len, d_model)
        pe = torch.zeros(max_len, d_model)

        # 偶数维度 (0, 2, 4, ...) 使用 sin 编码
        pe[:, 0::2] = torch.sin(position * div_term)
        # 奇数维度 (1, 3, 5, ...) 使用 cos 编码
        pe[:, 1::2] = torch.cos(position * div_term)

        # register_buffer 注册为非参数缓冲区，不会被 optimizer 更新
        # 但会随模型移动（to(device) 等操作）
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播：将位置编码添加到输入

        参数:
            x: 输入张量，形状 (batch_size, seq_len, d_model)

        返回:
            添加位置编码后的张量
        """
        # 将位置编码加到输入上，自动截取与输入序列长度匹配的部分
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


# ============================================================
# 编码器层 (Encoder Layer)
# ============================================================

class EncoderLayer(nn.Module):
    """
    编码器核心层

    每个编码器层包含两个子层：
    1. 多头自注意力层（Self-Attention）
    2. 位置前馈网络（Feed-Forward）

    每个子层周围有残差连接和层归一化：
    btc = LayerNorm(x + Sublayer(x))

    参数:
        d_model: 隐藏维度
        num_heads: 注意力头数
        d_ff: 前馈网络中间维度
        dropout: Dropout 比率
    """

    def __init__(self, d_model, num_heads, d_ff, dropout):
        """初始化编码器层"""
        super(EncoderLayer, self).__init__()  # 调用父类初始化

        # 自注意力层（Q=K=V=self）
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        # 前馈网络层
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)
        # 两个层归一化层
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        # Dropout 层
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask):
        """
        编码器层前向传播

        参数:
            x: 输入张量，形状 (batch_size, seq_len, d_model)
            mask: 掩码张量

        返回:
            编码器层输出
        """
        # 1. 多头自注意力子层：残差连接 + 层归一化
        attn_output = self.self_attn(x, x, x, mask)  # 自注意力：Q=K=V=x
        x = self.norm1(x + self.dropout(attn_output))  # 残差连接

        # 2. 前馈网络子层：残差连接 + 层归一化
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))  # 残差连接

        return x


# ============================================================
# 解码器层 (Decoder Layer)
# ============================================================

class DecoderLayer(nn.Module):
    """
    解码器核心层

    每个解码器层包含三个子层：
    1. 掩码多头自注意力层（Masked Self-Attention）
    2. 交叉注意力层（Cross-Attention）- 对编码器输出
    3. 位置前馈网络（Feed-Forward）

    参数:
        d_model: 隐藏维度
        num_heads: 注意力头数
        d_ff: 前馈网络中间维度
        dropout: Dropout 比率
    """

    def __init__(self, d_model, num_heads, d_ff, dropout):
        """初始化解码器层"""
        super(DecoderLayer, self).__init__()  # 调用父类初始化

        # 掩码自注意力层（对自己的注意力）
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        # 交叉注意力层（对编码器输出的注意力）
        self.cross_attn = MultiHeadAttention(d_model, num_heads)
        # 前馈网络层
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)
        # 三个层归一化层
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        # Dropout 层
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, encoder_output, src_mask, tgt_mask):
        """
        解码器层前向传播

        参数:
            x: 解码器输入张量，形状 (batch_size, tgt_seq_len, d_model)
            encoder_output: 编码器输出，形状 (batch_size, src_seq_len, d_model)
            src_mask: 源序列掩码
            tgt_mask: 目标序列掩码（用于防止看到未来位置）

        返回:
            解码器层输出
        """
        # 1. 掩码多头自注意力子层：只能看到当前位置及之前的位置
        attn_output = self.self_attn(x, x, x, tgt_mask)
        x = self.norm1(x + self.dropout(attn_output))  # 残差连接

        # 2. 交叉注意力子层：查询来自解码器，键值来自编码器输出
        cross_attn_output = self.cross_attn(x, encoder_output, encoder_output, src_mask)
        x = self.norm2(x + self.dropout(cross_attn_output))  # 残差连接

        # 3. 前馈网络子层
        ff_output = self.feed_forward(x)
        x = self.norm3(x + self.dropout(ff_output))  # 残差连接

        return x


# ============================================================
# 编码器 (Encoder)
# ============================================================

class Encoder(nn.Module):
    """
    完整编码器

    由词嵌入层、位置编码层和多个编码器层堆叠而成

    参数:
        vocab_size: 源语言词汇表大小
        d_model: 模型隐藏维度
        num_layers: 编码器层数
        num_heads: 注意力头数
        d_ff: 前馈网络中间维度
        dropout: Dropout 比率
        max_len: 最大序列长度
    """

    def __init__(self, vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len):
        """初始化编码器"""
        super(Encoder, self).__init__()  # 调用父类初始化

        # 词嵌入层：将词索引转换为嵌入向量
        self.embedding = nn.Embedding(vocab_size, d_model)
        # 位置编码层
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_len)
        # 多个编码器层堆叠
        self.layers = nn.ModuleList([
            EncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        # 最终的层归一化
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, mask):
        """
        编码器前向传播

        参数:
            x: 源序列词索引，形状 (batch_size, seq_len)
            mask: 掩码张量

        返回:
            编码器输出，形状 (batch_size, seq_len, d_model)
        """
        # 1. 词嵌入 + 位置编码
        x = self.embedding(x)
        x = self.pos_encoder(x)

        # 2. 通过所有编码器层
        for layer in self.layers:
            x = layer(x, mask)

        # 3. 最终归一化
        return self.norm(x)


# ============================================================
# 解码器 (Decoder)
# ============================================================

class Decoder(nn.Module):
    """
    完整解码器

    由词嵌入层、位置编码层和多个解码器层堆叠而成

    参数:
        vocab_size: 目标语言词汇表大小
        d_model: 模型隐藏维度
        num_layers: 解码器层数
        num_heads: 注意力头数
        d_ff: 前馈网络中间维度
        dropout: Dropout 比率
        max_len: 最大序列长度
    """

    def __init__(self, vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len):
        """初始化解码器"""
        super(Decoder, self).__init__()  # 调用父类初始化

        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, d_model)
        # 位置编码层
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_len)
        # 多个解码器层堆叠
        self.layers = nn.ModuleList([
            DecoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        # 最终的层归一化
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, encoder_output, src_mask, tgt_mask):
        """
        解码器前向传播

        参数:
            x: 目标序列词索引，形状 (batch_size, tgt_seq_len)
            encoder_output: 编码器输出
            src_mask: 源序列掩码
            tgt_mask: 目标序列掩码

        返回:
            解码器输出，形状 (batch_size, tgt_seq_len, d_model)
        """
        # 1. 词嵌入 + 位置编码
        x = self.embedding(x)
        x = self.pos_encoder(x)

        # 2. 通过所有解码器层
        for layer in self.layers:
            x = layer(x, encoder_output, src_mask, tgt_mask)

        # 3. 最终归一化
        return self.norm(x)


# ============================================================
# Transformer 主模型
# ============================================================

class Transformer(nn.Module):
    """
    完整 Transformer 模型

    由编码器、解码器和最终输出层组成

    参数:
        src_vocab_size: 源语言词汇表大小
        tgt_vocab_size: 目标语言词汇表大小
        d_model: 模型隐藏维度
        num_layers: 编码器/解码器层数
        num_heads: 注意力头数
        d_ff: 前馈网络中间维度
        dropout: Dropout 比率
        max_len: 最大序列长度
    """

    def __init__(self, src_vocab_size, tgt_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len=5000):
        """初始化 Transformer 模型"""
        super(Transformer, self).__init__()  # 调用父类初始化

        # 编码器
        self.encoder = Encoder(
            src_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len
        )
        # 解码器
        self.decoder = Decoder(
            tgt_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len
        )
        # 最终输出层：将 d_model 维度映射到目标词汇表大小
        self.final_linear = nn.Linear(d_model, tgt_vocab_size)

    def generate_mask(self, src, tgt):
        """
        生成掩码

        参数:
            src: 源序列，形状 (batch_size, src_len)
            tgt: 目标序列，形状 (batch_size, tgt_len)

        返回:
            src_mask: 源序列掩码
            tgt_mask: 目标序列掩码
        """
        # 源序列掩码：标记非零（有效）位置
        # 形状变换：(batch_size, src_len) -> (batch_size, 1, 1, src_len)
        src_mask = (src != 0).unsqueeze(1).unsqueeze(2)

        # 目标序列填充掩码
        # 形状变换：(batch_size, tgt_len) -> (batch_size, 1, 1, tgt_len)
        tgt_pad_mask = (tgt != 0).unsqueeze(1).unsqueeze(2)

        # 获取目标序列长度
        tgt_len = tgt.size(1)

        # 创建下三角矩阵，防止看到未来的 token（因果掩码）
        # 形状：(tgt_len, tgt_len)
        tgt_sub_mask = torch.tril(torch.ones((tgt_len, tgt_len), device=src.device)).bool()

        # 组合填充掩码和因果掩码
        tgt_mask = tgt_pad_mask & tgt_sub_mask

        return src_mask, tgt_mask

    def forward(self, src, tgt):
        """
        Transformer 前向传播

        参数:
            src: 源序列词索引，形状 (batch_size, src_seq_len)
            tgt: 目标序列词索引，形状 (batch_size, tgt_seq_len)

        返回:
            输出 logits，形状 (batch_size, tgt_seq_len, tgt_vocab_size)
        """
        # 1. 生成掩码
        src_mask, tgt_mask = self.generate_mask(src, tgt)

        # 2. 通过编码器
        encoder_output = self.encoder(src, src_mask)

        # 3. 通过解码器
        decoder_output = self.decoder(tgt, encoder_output, src_mask, tgt_mask)

        # 4. 最终线性变换映射到词汇表大小
        output = self.final_linear(decoder_output)

        return output


# ============================================================
# 演示代码
# ============================================================

if __name__ == "__main__":
    # 1. 定义超参数（与原始论文一致）
    src_vocab_size = 5000   # 源语言词汇表大小
    tgt_vocab_size = 5000   # 目标语言词汇表大小
    d_model = 512           # 隐藏维度
    num_layers = 6          # 编码器/解码器层数
    num_heads = 8           # 注意力头数
    d_ff = 2048             # 前馈网络中间维度（d_model 的 4 倍）
    dropout = 0.1           # Dropout 比率
    max_len = 100            # 最大序列长度

    # 2. 实例化模型
    model = Transformer(
        src_vocab_size, tgt_vocab_size, d_model,
        num_layers, num_heads, d_ff, dropout, max_len
    )

    # 3. 创建模拟输入数据
    # 批次大小=2，源序列长度=10，目标序列长度=12
    src = torch.randint(1, src_vocab_size, (2, 10))   # (batch_size, src_seq_len)
    tgt = torch.randint(1, tgt_vocab_size, (2, 12))   # (batch_size, tgt_seq_len)

    # 4. 前向传播
    output = model(src, tgt)

    # 5. 打印输出形状
    # 输出形状：(2, 12, 5000) = (batch_size, tgt_seq_len, tgt_vocab_size)
    print("模型输出的形状:", output.shape)
