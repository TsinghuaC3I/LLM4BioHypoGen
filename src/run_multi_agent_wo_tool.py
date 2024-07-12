#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-09-11 17:38:24
# @Author  : Kaiyan Zhang (zhang-ky22@mails.tsinghua.edu.cn)
# @Link    : https://github.com/iseesaw
import os
import re
import srsly
from tqdm import tqdm

from typing import List, Dict, Callable
from collections import OrderedDict
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

from src.agents.dialogue_agent_with_tool import DialogueAgentWithTools
from src.agents.dialogue_agent import DialogueAgent
from src.environment import DialogueSimulator
from src.prompts_wo_tool import prompt_critic, prompt_analyst, prompt_scientist, prompt_env

def main(background):
    names = OrderedDict({
        "analyst": {
            "name": "Analyst",
            "system_message": prompt_analyst,
            "tools": None
            },
        "scientist": {
            "name": "Scientist",
            "system_message": prompt_scientist,
            "tools": None},
        "critic": {
            "name": "Critic",
            "system_message": prompt_critic,
            "tools": None}})

    # we set `top_k_results`=2 as part of the `tool_kwargs` to prevent results from overflowing the context limit
    agents = [
        DialogueAgent(
            name=names["analyst"]["name"], 
            system_message=SystemMessage(content=names["analyst"]["system_message"]), 
            model=ChatOpenAI(model_name="gpt-3.5-turbo-0613", temperature=0.2)),
        DialogueAgent(
            name=names["scientist"]["name"], 
            system_message=SystemMessage(content=names["scientist"]["system_message"]), 
            model=ChatOpenAI(model_name="gpt-3.5-turbo-0613", temperature=0.2)),
        DialogueAgent(
            name=names["critic"]["name"], 
            system_message=SystemMessage(content=names["critic"]["system_message"]), 
            model=ChatOpenAI(model_name="gpt-3.5-turbo-0613", temperature=0.2))
    ]

    def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:
        idx = (step) % len(agents)
        return idx
    
    conversation_description = prompt_env.format(background=background)
    
    simulator = DialogueSimulator(agents=agents, selection_function=select_next_speaker)
    simulator.reset()
    simulator.inject("Moderator", conversation_description)
    print(f"(Moderator): {conversation_description}")
    print("\n")

    max_iters = 20
    n = 0
    hypothesis = None
    messages = []
    while n < max_iters:
        name, message = simulator.step()
        messages.append({"name": name, "message": message})
        print(f"({name}): {message}")
        print("\n")
        n += 1
        if name == "Critic" and "Final Answer:" in message:
            # Adjusting the regular expression to extract all hypothesis points between the delimiters
            hypothesis = message.split("Final Answer:")[-1].replace("\n", "")
            print(">>>>>>>>>>>>>>>\n", hypothesis, "\n\n")
            break
    return hypothesis, messages

if __name__ == "__main__":
    # data = list(srsly.read_jsonl("data/gpt-4/test_unseen.jsonl"))
    data = [
        {
            "input": "(1) Esophageal cancer mainly includes squamous cell carcinoma and adenocarcinoma, with different risk factors and incidence rates. (2) Metformin has been shown to reduce the risk of several cancers in patients with T2DM. (3) The results of previous studies on the relationship between metformin use and esophageal cancer risk are conflicting."
        }
    ]
    outputs = []
    for idx, ex in tqdm(enumerate(data), total=len(data)):
        try:
            output, messages = main(ex["input"].replace(":", ""))
            ex["multi_agent"] = output
            ex["messages"] = messages
        except Exception as e:
            print(idx, e)
        finally:
            outputs.append(ex)
    srsly.write_jsonl("unseen_multi_agent.jsonl", outputs)