"""提示词集合。

本文件中的提示词逐字复制自原仓库：
  Dr.ECI/agent1/prompt.py   （Causal Explorer：causal / causation / causality + system + vanilla_formal）
  Dr.ECI/agent2/prompt.py   （Mediator Detector）
  Dr.ECI/agent3/prompt.py   （Direct / Indirect Reasoner）
除函数签名外，未对提示词文本做任何改写。
"""

# ---------------------------------------------------------------- agent1: Causal Explorer
def causal(source, target, text):
    prompt = f'''
"text": {text}
"source event": {source},
"target event": {target},

Question: Is there a causal relationship between {source} and {target} ? 

    '''
    return prompt


def causation(source, target, text):
    prompt = f'''
"text": {text}
"source event": {source},
"target event": {target},
Question: Is there causation between {source} and {target} ? 

    '''
    return prompt


def causality(source, target, text):
    prompt = f'''
"text": {text}
"source event": {source},
"target event": {target},

Question: Is there causality between {source} and {target} ? 

    '''
    return prompt


explorer_system = '''
You are an expert at identifying cause-effect relationships between events in a text. Please answer this question based on the context given to you.
'''

vanilla_formal = "Your final answer should be {{\"Answer\":\"Yes\"}} or {{\"Answer\":\"No\"}}, in the format of JSON {{\"Answer\":\" \"}}, at the end of your reply."

# ---------------------------------------------------------------- agent2: Mediator Detector
mediator_system = "You are an expert in Entity Extraction. You are good at extracting entities associated with source event and target event from the context text given to you. Note that the associated entities are at word level."


def mediator(source, target, text):
    prompt = f'''
 "text": {text}
"source event": {source},
"target event": {target},   
Question: Please give the entity that the source event and target event are related to.
###
Please follow the following process to answer the  Question:

        - Subquestion 1:Please search for all events or entities associated with the event "{source}" from "{text}", except the event "{source}" itself.
        - Answer to subquestion 1:(answer me at word level, such as "stay", "begged", "locked up","John","person".)

        - Subquestion 2:Please search for all events or entities associated with the event "{target}" from "{text}", except the event "{target}" itself.
        - Answer to subquestion 2:(answer me at word level, such as "stay", "begged", "locked up","John","person".)

        - Subquestion 3:Please find all events or entities in '{text}' that are associated with event '{source}' and event '{target}', except event '{source}' and event '{target}' themselves.
        - Answer to subquestion 3:(answer me at word level, such as "stay", "begged", "locked up","John","person".)

        - Subquestion 4: According to the previous Subquestion 3, if there are entities associated with event '{source}' and event '{target}', except event '{source}' and event '{target}' themselves. Give these entities in json format, such as {{["Entity 1", "Entity 2",...]}}. If they do not exist, answer directly {{"No"}}.
        - Answer to subquestion 4:
    '''
    return prompt


mediator_formal = "If there are related events or entities, please save them directly in JSON format, such as {{[\"entity 1\",\"entity 2\", ...]}}. If not, just answer No directly, such as {{\"Answer\":\"None\"}}."

# ---------------------------------------------------------------- agent3: Reasoner
reasoner_system = '''You are an expert at identifying causal relationships between events in text, both implicit and explicit. Please answer this question based on the context you are given. '''


def reasoner(source, target, text, mediator_both):
    prompt = f'''

###
Please follow the following rules to answer the Question:
    - **According to each given causal rule, determine whether there is a causal relationship between X({source}) and Y({target}):**
    (If Z exists, determine which of the following rules each Z can satisfy with events X and Y. If Z does not exist, directly analyze what rules are satisfied between X and Y.)

where:
    - TEXT: {text}
    - X: {source}
    - Y: {target}
    - Z: {mediator_both}

- Rules:
        - Rule 1: Explicit Causation Words
            */In the text, there are verbs or verb phrases that clearly express causality, and they relate X and Y. The relationship between them can be expressed as: X cause/lead/due to (Explicit causation words) Y. So there is a causal relationship between X and Y.Explicit causation words(In addition to X and Y themselves, verbs or verb phrases that can clearly express causal relationships.):
            "cause," "result," "lead," "create," "cause by," "lead to," "result in," "due to", "because of","by", etc.*/
        - Answer to Rule 1: (If this rule is met, please give {{\"Rule 1\":\"Explicit Causation Words\"}} in JSON format, otherwise answer {{\"No\"}}.

        - Rule 2: Implicit Causation Words
            */There are implicit clue words in the text that imply a causal relationship, and they associate X and Y. These implicit clue words are expressed in natural language as being likely to cause event X and event Y to have a causal relationship. The relationship between them can be expressed as: X aggravate/force/provoke (Implicit causation words) Y. So there is a causal relationship between X and Y.Implicit causation words(In addition to X and Y themselves, verbs or verb phrases that implicitly express causal relationships can be used.):
            "spark," "aggravate," "stir," "precipitate," "ignite," "pave," "exacerbate," "force ," "arouse," "worsen," "result from," "reduce," "provoke," "inflict," "fuel," "stem," "prompt," "alleviate," "trigger," "increase with ," "contribute to" etc.*/
        - Answer to Rule 2: (If this rule is met, please give {{\"Rule 2\":\"Implicit Causation Words\"}} in JSON format, otherwise answer {{\"No\"}}.

        - Rule 3: Causal Order( or common sense knowledge)
            */According to common sense knowledge, if event X occurs before event Y and can be expressed as: X causes Y, then there is a causal relationship between X and Y. If the expression "X causes Y" does not follow common sense or is incorrectly expressed, then there is no causal relationship between them. */
        - Answer to Rule 3: (If this rule is met, please give {{\"Rule 3\":\"Causal Order\"}} in JSON format, otherwise answer {{\"No\"}}.

        - Rule 4: The Coreference event of event X
            */In the text, if an event with the same or similar meaning as the X can be found, and this similar event has a causal relationship with the Y event, then there is also a causal relationship between the X and the Y.*/
        - Answer to Rule 4: (If this rule is met, please give {{\"Rule 4\":\"The Coreference event of event X\"}} in JSON format, otherwise answer {{\"No"}}.

        - Rule 5: The Coreference event of event Y
        */In the text, if an event with the same or similar meaning as the Y can be found, and this similar event has a causal relationship with the X, then there is also a causal relationship between the X and the Y.*/
        - Answer to Rule 5: (If this rule is met, please give {{\"Rule 5\":\"The Coreference event of event Y\"}} in JSON format, otherwise answer {{\"No"}}.

        - Rule 6: Chain
        */In "text", there is an entity or event(Z) that both events X and Y are related to.  First,it satisfies that it is related to X and Y respectively, then it satisfies that X acts on Z and Z acts on Y, and finally they form a causal chain: X->Z->Y. Therefore, it can be concluded that there is a causal relationship between X and Y. */
        - Answer to Rule 6: (If this rule is met, please give {{\"Rule 6\":\"Chain\"}} in JSON format, otherwise answer {{\"No"}}.

        - Rule 7: Collider
        */In "text", there is an entity or event(Z) that both events X and Y are related to.  First, it satisfies that it is related to X and Y respectively, and then it satisfies that X acts on Z and Y acts on Z. Finally, X, Z and Y form the Collider structure. Therefore, it can be concluded that there is a causal relationship between X and Y.*/
        - Answer to Rule 7: (If this rule is met, please give {{\"Rule 7\":\"Collider\"}} in JSON format, otherwise answer {{\"No"}}.

        - Rule 8: Fork
        */In "text", there is an entity or event(Z) that both events X and Y are related to. First, it satisfies that it is related to X and Y respectively, and then it satisfies that Z acts on X and Z acts on Y. Finally X, Z and Y form the Fork structure. Therefore, it can be concluded that there is a causal relationship between X and Y.*/
        - Answer to Rule 8: (If this rule is met, please give {{\"Rule 8\":\"Fork\"}} in JSON format, otherwise answer {{\"No"}}.        
    
        - Give your analysis first, and finally give the answer in JSON format. 
 '''

    return prompt
