from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from lang_graph.node import understand_query_node, tavily_search_node, generate_answer_node
from lang_graph.state import SearchState



# 构建搜索工作流
def create_search_assistant():
    workflow = StateGraph(SearchState)

    # 添加三个节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    # 编译图
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app