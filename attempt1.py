import logging
import argparse
import utils
import asyncio
import google.generativeai as ai
import time
import dotenv
import os

dotenv.load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
ai.configure(api_key=API_KEY)

class LLM:
    @staticmethod
    async def call(input: str) -> str:
        model = ai.GenerativeModel("gemini-1.5-flash")
        model._generation_config
        response = await model.generate_content_async(input)
        return response.candidates[0].content.parts[0].text

    @staticmethod
    async def test(prompt: str):
        start_time = time.time()
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        model = ai.GenerativeModel("gemini-1.5-flash")
        response = await model.generate_content_async(prompt)
        end_time = time.time()
        print(f"Ended at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"Duration: {end_time - start_time:.2f} seconds")
        print(response.candidates[0].content.parts[0].text)


class Register:
    """
    Registers are used to store data. They can be set, added to, cleared, and read.
    Registers are created with a name and a description.
    Register names must be unique, and are used to access the register.
    Register descriptions are used to describe the contents of the register.
    """
    def __init__(self, name: str, description: str, size: int = 1000):
        self.content: str = ""
        self.name = name
        self.description = description
        self.size = size
        self.locked_to: str = ""
        logging.debug(f"Creating register {self.name}")
        logging.info(f"Register {self.name} created")

    def lock_to_process(self, pid: str):
        self.locked_to = pid
        logging.debug(f"Locking register {self.name} to process {pid}")
        logging.info(f"Locking register {self.name} to process {pid}")

    def __check_lock(self, pid: str):
        if pid != self.locked_to:
            logging.error(f"Process {pid} does not have lock on register {self.name}")
            raise ValueError(f"Process {pid} does not have lock on register {self.name}")

    def set(self, value: str, pid: str):
        self.__check_lock(pid)
        if len(value) > self.size:
            logging.error(f"Value too large for register {self.name}")
            raise ValueError(f"Value too large for register {self.name}")
        self.content = value
        logging.debug(f"Setting register {self.name} to {value}")
        logging.info(f"Setting register {self.name}")

    def add(self, value: str, pid: str):
        self.__check_lock(pid)
        if len(self.content) + len(value) > self.size:
            logging.error(f"Value too large for register {self.name}")
            raise ValueError(f"Value too large for register {self.name}")
        self.content += value
        logging.debug(f"Adding {value} to register {self.name}")
        logging.info(f"Adding to register {self.name}")

    def content_size(self):
        return len(self.content)

    def clear(self, pid: str):
        self.__check_lock(pid)
        self.content = ""
        logging.debug(f"Clearing register {self.name}")
        logging.info(f"Clearing register {self.name}")

    def get(self):
        return self.content
    

    
    def __str__(self):
        return str(self.content)



class Thought:
    def __init__(self,owner_name: int, information: str, summary_size: int = 300, opinion_size: int = 400, inference_margin: float = 0.1):
        self.information = information
        self.summary_size = summary_size * (1 - inference_margin)
        self.opinion_size = opinion_size * (1 - inference_margin)
        self.owner_name = owner_name

    async def trigger(self):
        """Trigger must be called to generate the summary and opinion. Context will generally be included as part of 'information' to the call."""
        summary = await LLM.call(f'Summarize this information in under {self.summary_size} characters: {self.information}')
        self.summary = summary
        opinion = await LLM.call(f'What do you think about this information in under {self.opinion_size} characters: {self.information}')
        self.opinion = opinion

    def __str__(self):
        return f"<info> {self.information} <info>  <opinion>{self.opinion} <opinion>"

class ChannelIn:
    pass

class ChannelOut:
    pass

class Angel:
    def __init__(self, name: str, goal: str,  manager: 'Chuck'):
        self.name = name
        self.goal = goal
        self.manager = manager
        self.manager_messages: list[str] = []
        self.locked_registers: list[str] = []
        self.locked_channels: list[str] = []

    def smite(self):
        for register in self.locked_registers:
            self.manager.call_release_register_lock(register)
        for channel in self.locked_channels:
            self.manager.call_release_channel_lock(channel)

    def __ask_for_register_lock(self, register_name: str, reason: str):
        self.manager.req_ask_for_register_lock(self.name, register_name, reason)

    def __ask_for_channel_lock(self, channel_name: str):
        self.manager.req_ask_for_channel_lock(channel_name)

    def __release_channel_lock(self, channel_name: str):
        self.manager.call_release_channel_lock(channel_name)
        self.locked_channels.remove(channel_name)
    
    def __release_register_lock(self, register_name: str):
        self.manager.call_release_register_lock(register_name)


class Chuck:
    def __init__(self,
                goal: str):
        self.goal = goal
        self.memory: dict[str, Register] = {}
        self.memory_locks: dict[str, str] = {} # register_name: child_name

        self.pub_thoughts: dict[str, Thought] = {}
        self.child_message_queue: dict[str, str] = {}
        self.priv_thoughts: dict[str, Thought] = {}

        self.InChannels: dict[str, ChannelIn] = {}
        self.OutChannels: dict[str, ChannelOut] = {}
        self.channel_locks: dict[str, str] = {} # channel_name: child_name

        self.name_generator = utils.NameGenerator()
        self.children: dict[str, Angel] = {}

    async def child_lifecycle(self):
        OPTIONS = """
1. __spawn_process(goal: str)
A child process is created with the given name and goal.
The child process will process information and communicate with the parent process using sys calls.
The child process will be added to the list of child processes.

2. __kill_process(name: str)
The child process with the given name is killed.
"""
        KNOWLEDGE = f"""
GOAL: {self.goal}
CHILDREN: {self.children}
MESSAGES FROM CHILDREN: {self.child_message_queue}
"""
        EXAMPLE = """__spawn_process("Figure out what we should do with the new information")
__spawn_process("Where can we find more information on this topic?")
__kill_process("michael")
"""
        EXTRA= "Do not include any extraneous information. Do not give children the same task."
        resp = await LLM.call(f"Context: {KNOWLEDGE}. Choose from options, can choose multiple: {OPTIONS}. Example response: {EXAMPLE}. Extra: {EXTRA}")
        resp = resp.split("\n")
        print(resp)
        for r in resp:
            if "__spawn_process" in r:
                goal= r.removeprefix("__spawn_process(").removesuffix(")")
                self.__spawn_process(goal)
            elif "__kill_process" in r:
                name= r.removeprefix("__kill_process(").removesuffix(")")
                self.__kill_process(name)

    async def register_lifecycle(self):
        OPTIONS = """
1. __create_register(name: str, description: str)
A register is created with the given name and description. Registers are used for storing general information that might be useful to children.
The register is added to the list of registers.
2. __consolidate_registers(list_of_registers: list[str], new_register_name: str)
The registers in the list are consolidated into a new register with the given name.
The new register is added to the list of registers.
The old registers are deleted.
3. __delete_register(name: str)
The register with the given name is deleted.
"""
        KNOWLEDGE = f"""
GOAL: {self.goal}
REGISTERS: {self.memory}
PUBLIC IDEAS: {self.pub_thoughts}
PRIVATE IDEAS: {self.priv_thoughts}
"""
        EXAMPLE = """__create_register("thoughts", "A register to store thoughts")
__consolidate_registers(["favorite_exercises", "favorite_foods"], "favorite_things")
__delete_register("fish")
"""
        resp = await LLM.call(f"Context: {KNOWLEDGE}. Choose from options, can choose multiple: {OPTIONS}. Example response: {EXAMPLE} Do not include any extraneous information.")
        resp = resp.split("\n")
        print(resp)
        for r in resp:
            if "__create_register" in r:
                name= r.removeprefix("__create_register(").split(",")[0].replace('"', "")
                description= r.removeprefix("__create_register(").split(",")[1].removesuffix(")")
                self.memory[name] = Register(name, description)
                self.__create_register(name, description)
            elif "__consolidate_registers" in r:
                list_of_registers= r.removeprefix("__consolidate_registers(").split(",")[0]
                new_register_name= r.removeprefix("__consolidate_registers(").split(",")[1].removesuffix(")")
                print("NOT IMPLEMENTED")
            elif "__delete_register" in r:
                name= r.removeprefix("__delete_register(").removesuffix(")")
                print("NOT IMPLEMENTED")

    async def child_communication_lifecycle(self):
        OPTIONS = """
1. __grant_register_lock(register_name: str, child: str)
The register with the given name is locked to the child process with the given name.
The register lock is a sempaphore to protect concurrent access to the register. Only one child can have access to the register at a time.
This allows to write to the register.

2. __force_release_register_lock(register_name: str)
The register with the given name is forcefully released.

3. __send_message(name: str, message: str)
The child process with the given name is sent the given message.
"""
        KNOWLEDGE = f"""
GOAL: {self.goal}
CHILDREN: {self.children}
MESSAGES FROM CHILDREN: {self.child_message_queue}
"""
        EXAMPLE = """__grant_register_lock("thoughts", "michael")
__force_release_register_lock("project_facts")
__send_message("michael", "What do you think about the new information?")
"""
        EXTRA= "Do not include any extraneous information. Do not send a message with no purpose."
        resp = await LLM.call(f"Context: {KNOWLEDGE}. Choose from options, can choose multiple: {OPTIONS}. Example response: {EXAMPLE}. Extra: {EXTRA}")
        print(resp)
        resp = resp.split("\n")
        for r in resp:
            if "__grant_register_lock" in r:
                register_name= r.removeprefix("__grant_register_lock(").split(",")[0].replace('"', "").replace(" ", "")
                child= r.removeprefix("__grant_register_lock(").split(",")[1].removesuffix(")").replace('"', "").replace(" ", "")
                logging.debug(f"Register lock requested for {register_name} by {child}")
                self.__grant_register_lock(register_name, child)

            elif "__force_release_register_lock" in r:
                register_name= r.removeprefix("__force_release_register_lock(").removesuffix(")")
                logging.debug(f"Force releasing register {register_name}")
                self.__force_release_register_lock(register_name)

            elif "__send_message" in r:
                name= r.removeprefix("__send_message(").split(",")[0].replace('"', "").replace(" ", "")
                message= r.removeprefix("__send_message(").split(",")[1].removesuffix(")")
                logging.debug(f"Sending message to {name}, {message}")
                self.__send_message(name, message)

    async def chuck_lifecycle(self):
        await self.child_lifecycle()
        await self.register_lifecycle()
        await self.child_communication_lifecycle()
        

    def __spawn_process(self, goal: str):
        name = self.name_generator.generate_name()
        logging.debug(f"Spawning process {name} with goal {goal}")
        child = Angel(name=name, goal=goal, manager=self)
        self.children[name] = child
        logging.info(f"Spawned {name} created with goal {goal}")

    def __kill_process(self, name: str):
        logging.debug(f"Killing {name}")

        self.children[name].smite()
        del self.children[name]
        logging.info(f"Killed {name}")

    def __send_message(self, name: str, message: str):
        logging.debug(f"Sending message to process {name}")
        logging.info(f"Sending message to process {name}: {message}")
        if len(self.children[name].manager_messages) > 10:
            self.children[name].manager_messages.pop(0)
        self.children[name].manager_messages.append(message)

    def __create_register(self, name: str, description: str):
        logging.debug(f"Creating register {name}")
        self.memory[name] = Register(name, description)
        logging.info(f"Created register {name}")

    def req_ask_for_register_lock(self, child: str, register_name: str, reason: str):
        self.child_message_queue[child] = f"requesting: __grant_register_lock({register_name}, {child}) reason: {reason}"
         
        if register_name not in self.memory_locks.keys():
            message = f"Register {register_name} is not currently locked by any child. Use __grant_register_lock(register_name: str, child: str) to grant access."
            logging.debug(message)
            self.child_message_queue['self'] = message
        else:
            message = f"Register {register_name} is currently locked by {self.memory_locks[register_name]}. Use __force_release_register_lock(register_name: str) to force release it."
            logging.debug(message)
            self.child_message_queue['self'] = message

    def __grant_register_lock(self, register_name: str, child: str):
        self.memory_locks[register_name] = child
        self.children[child].locked_registers.append(register_name)
        logging.info(f"Register {register_name} locked to {child}")

    def __force_release_register_lock(self, register_name: str):
        child_locker = self.memory_locks[register_name]
        self.children[child_locker].__release_register_lock(register_name)
        self.memory_locks.pop(register_name)


    def call_release_register_lock(self, register_name: str):
        self.__force_release_register_lock(register_name)
        pass

    def call_add_public_thought(self, thought_name: str, thought: Thought):
        self.pub_thoughts[thought_name] = thought

    def req_ask_for_channel_lock(self, channel_name: str):
        pass

    def __grant_channel_lock(self, channel_name: str, child: str):
        pass

    def call_release_channel_lock(self, channel_name: str):
        pass


    
def main():
    parser = argparse.ArgumentParser(description="Register script with logging.")
    parser.add_argument('--log-level', default='WARNING', help='Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), None))
    chuck = Chuck(goal="Create a new fitness app.")
    async def run_lifecycle():
        #while True:
        await chuck.chuck_lifecycle()



    asyncio.run(run_lifecycle())

if __name__ == "__main__":
    main()