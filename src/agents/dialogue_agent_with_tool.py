#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-09-11 17:37:00
# @Author  : Kaiyan Zhang (zhang-ky22@mails.tsinghua.edu.cn)
# @Link    : https://github.com/iseesaw

from typing import List, Dict, Callable
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)
from langchain.agents import Tool
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.agents import load_tools

from src.agents.dialogue_agent import DialogueAgent

class DialogueAgentWithTools(DialogueAgent):
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: ChatOpenAI,
        # tool_names: List[str],
        tools,
        **tool_kwargs,
    ) -> None:
        super().__init__(name, system_message, model)
        self.tools = tools #load_tools(tool_names, **tool_kwargs)

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        agent_chain = initialize_agent(
            self.tools,
            self.model,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            ),
            handle_parsing_errors=True
        )
        message = AIMessage(
            content=agent_chain.run(
                input="\n".join(
                    [self.system_message.content] + self.message_history + [self.prefix]
                )
            )
        )

        return message.content

