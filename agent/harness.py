from concurrent.futures import ThreadPoolExecutor

from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.tools import Tool
from datapizza.type import ROLE, Block, FunctionCallBlock, FunctionCallResultBlock
from datapizza.type.type import TextBlock

from agent.custom_logs import log_answer, log_tool_call_invoke, log_tool_call_result


class Agent:
    def __init__(
        self,
        client: OpenAIClient,
        system_prompt: str,
        tools: list[Tool],
        compact_logs: bool = False,
        max_tool_workers: int = 8,
        name: str = "",
    ):
        self.tool_mapping = {tool.name: tool for tool in tools}
        self.tools = tools
        self.client = client
        self.memory = Memory()
        self.tool_executor = ThreadPoolExecutor(max_workers=max_tool_workers)
        self.system_prompt = system_prompt
        self.compact_logs = compact_logs
        self.name = name

    def _execute_tool_call(
        self,
        block: FunctionCallBlock,
    ) -> FunctionCallResultBlock:
        tool_name = block.name
        tool = self.tool_mapping[tool_name]
        tool_args = block.arguments

        log_tool_call_invoke(
            tool_name, tool_args, compact=self.compact_logs, agent_name=self.name
        )
        result = tool(**tool_args)
        log_tool_call_result(
            tool_name, result, compact=self.compact_logs, agent_name=self.name
        )

        return FunctionCallResultBlock(
            id=block.id,
            tool=tool,
            result=result,
        )

    def _step(
        self, input: str | None = None, memory: Memory | None = None
    ) -> tuple[list[Block], list[FunctionCallResultBlock]]:
        response = self.client.invoke(
            input=input,
            tools=list(self.tool_mapping.values()),
            memory=memory,
            system_prompt=self.system_prompt,
        )
        output = []
        tool_futures = []
        for block in response.content:
            output.append(block)
            if isinstance(block, FunctionCallBlock):
                tool_futures.append(
                    self.tool_executor.submit(self._execute_tool_call, block)
                )

            elif isinstance(block, TextBlock):
                log_answer(
                    block.content, compact=self.compact_logs, agent_name=self.name
                )

        tool_results = [future.result() for future in tool_futures]

        return output, tool_results

    def run(self, input: str) -> str:
        self.memory.add_turn(TextBlock(content=input), ROLE.USER)
        while True:
            step_result, tool_results = self._step(memory=self.memory)
            self.memory.add_turn(step_result, ROLE.ASSISTANT)
            if tool_results:
                for tool_result in tool_results:
                    self.memory.add_turn(tool_result, ROLE.TOOL)
            else:
                output_text = ""
                for block in step_result:
                    if isinstance(block, TextBlock):
                        output_text += block.content
                return output_text
