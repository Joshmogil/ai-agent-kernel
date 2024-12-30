import google.generativeai as ai
import time
import dotenv
import os
import asyncio
import logging
import argparse
from typing import Tuple
import inspect
import subprocess
import utils

dotenv.load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
ai.configure(api_key=API_KEY)


Id=str

PipelineTask = tuple[Id,str]

class LLM:

    @staticmethod
    async def prompt(prompt: str):
        start_time = time.time()
        logging.debug(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        model = ai.GenerativeModel("gemini-1.5-flash")
        response = await model.generate_content_async(prompt)
        end_time = time.time()
        logging.debug(f"Ended at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        logging.debug(f"Duration: {end_time - start_time:.2f} seconds")
        logging.debug(response.candidates[0].content.parts[0].text)
        return response.candidates[0].content.parts[0].text

    @staticmethod
    async def multi_prompt(prompts: list[PipelineTask]):
        tasks = [LLM.prompt(prompt[1]) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        prompt_result_dict = dict(zip([prompt[0] for prompt in prompts], results))
        return prompt_result_dict

# -- 
class Chuck:
    
    def __init__(self):
        self.pipeline: list[PipelineTask] = []
        self.recent_result_set: dict[id, str]
        self.time: int = 0
        
    def add(self, task_id: str, prompt: str):
        self.pipeline.append((task_id,prompt))

    def lookup(self, task_id: str):
        return self.recent_result_set.get(task_id)


    async def run(self):
        logging.info(f"Running pipeline with {len(self.pipeline)} tasks, day {self.time}.")
        self.recent_result_set= await LLM.multi_prompt(self.pipeline)
        logging.info(F"Pipeline finished running")
        self.pipeline=[]
        self.time+=1

class IO:
    def __init__(self):
        pass
    
    def __reflect__(self):
        return inspect.getsource(type(self))
    
class Terminal(IO):
    def __init__(self):
        super().__init__()

    def execute(self, command: str) -> str:
        """Execute a command in the shell. Each command gets a new shell."""
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.stderr

class Angel:
    def __init__(self, goal: str, narrow_goal: str, global_info: str, name: str, thought_depth: int = 4):
        self.name = name
        self.thoughts: list[str] = []
        self.goal = goal
        self.narrow_goal = narrow_goal
        self.global_info = global_info
        self.think_task_id: Id = ""
        self.thought_depth = thought_depth
        self.in_danger = False

    def think(self) -> PipelineTask:
        new_id = utils.get_random_id()
        if not self.in_danger:        
            prompt = f"Information: {self.global_info}\nGoal: {self.goal}\nPrevious Thoughts:{'/n'.join(self.thoughts)}"
        if self.in_danger:
            prompt = f"Information: {self.global_info}\nGoal: {self.goal}\nPrevious Thoughts:{'/n'.join(self.thoughts)}\nPlease explain why what you are working on is aligned with our goal, if it is not you will be destroyed."
        self.think_task_id = new_id
        return (new_id,prompt)
    
    def add_thoughts(self, thought: str):
        self.thoughts.append(thought)
        if len(self.thoughts) > self.thought_depth:
            self.thoughts.pop(0)

    def __str__(self):
        return f"Angel Name: {self.name}. Angel Thoughts: {self.thoughts}"
        
class Metatron:
    """Responsible for condensing information."""
    pass

class Lucifer:
    """Responsible for killing angels."""
    def __init__(self, goal: str, global_info: str):
        self.goal = goal
        self.global_info = global_info
        self.examine_angels_task_id: Id = ''
        self.evaluate_angel_pleas_task_id: Id = ''

    def examine_angels(self, angels: list[Angel]) -> PipelineTask:
        prompt=f"Our goal is to {self.goal}. Carefully review each angel's thoughts and respond with a list of names. Which should be examined if they aren't aligned with our goal. Your list should be a space seprated list of names, e.g. 'Michael Gabriel Raphael'"
        for angel in angels:
            if angel.in_danger == False:
                prompt = prompt + '\n' + str(angel)
        task_id = utils.get_random_id()
        self.examine_angels_id = task_id
        return (task_id,prompt)
    
    def mark_angels_for_danger(self, angels: list[Angel], angels_to_mark: list[str]):
        for angel in angels:
            if angel.name in angels_to_mark:
                angel.in_danger = True
        
    def evaluate_angel_pleas(self, angels: list[Angel]) -> PipelineTask:
        prompt = f"Our goal is to {self.goal}. Review each angel's plea for life and provide a list of angels who's pleas are insufficient given our goal, these angels will be destroyed. Your list should be a space seprated list of names, e.g. 'Michael Gabriel Raphael'"
        for angel in angels:
            if angel.in_danger == True:
                prompt = prompt + '\n' + str(angel)
        task_id = utils.get_random_id()
        self.evaluate_angel_pleas_task_id = task_id
        return (task_id,prompt)
    
    def destroy_angels(self, angels: list[Angel], angels_to_destroy: list[str]):
        for angel in angels:
            if angel.name in angels_to_destroy:
                angels.remove(angel)

class Jack:
    """Responsible for creating angels."""
    def __init__(self, goal: str, global_info: str):
        self.goal = goal
        self.global_info = global_info
        self.create_angels_task_id: Id = ''

    def decide_to_create_angels(self, angels: list[Angel]) -> PipelineTask:
        example= [{
            "name": "Castiel",
            "goal": "Save Dean",
            },
            {
            "name": "Michael",
            "goal": "Defeat Lucifer",
            }
            ]

        prompt = f"Our goal is to {self.goal}. Carefully review each angel's thoughts and decide if we need more angels to tackle our goal. If you decide we need more angels, provide a dictionary of the following format: \n {example}. Response must be json compliant and fit the format. Angel names must be unique"
        for angel in angels:
            prompt = prompt + '\n' + str(angel)
        
        task_id = utils.get_random_id()
        self.create_angels_task_id = task_id
        return (task_id,prompt)
    
    def create_angels(self, angels_info, angels: list[Angel]):
        for angel_info in angels_info:
            angel = Angel(
                narrow_goal=angel_info['goal'],
                name=angel_info['name'],
                goal=self.goal,
                global_info=self.global_info
                )
            angels.append(angel)



class Castiel:
    """Responsible for taking action"""
    pass


def get_current_file_source():
    import sys
    current_file = sys.modules[__name__].__file__
    with open(current_file, 'r') as file:
        return file.read()

# Run the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register script with logging.")
    parser.add_argument('--log-level', default='WARNING', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), None))
    goal=f"Review your own source code: {get_current_file_source()}"


    global_info=get_current_file_source()


    chuck = Chuck()

    jack = Jack(goal=goal, global_info=global_info)
    lucifer = Lucifer(goal=goal, global_info=global_info)

    angels :list[Angel] = []
    while True:
        input("Press enter to continue")
        print(f"year {chuck.time}")
        jpt1 = jack.decide_to_create_angels(angels)
        chuck.add(jpt1[0],jpt1[1])
        
        if len(angels) == 0:
            logging.info("No angels to evaluate.")
            asyncio.run(chuck.run())
            angel_task=chuck.lookup(jack.create_angels_task_id)
            jack.create_angels(angel_task,angels)
            continue

        if len(angels) > 0:
            lpt1 = lucifer.examine_angels(angels)
            chuck.add(lpt1[0],lpt1[1])

