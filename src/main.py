# -*- coding: utf-8 -*-
from webdriver import Webdriver
from database_model import Persona
from log import parse_log
import subprocess

def get_docker_id():
    bashCommand = "head -1 /proc/self/cgroup|cut -d/ -f3"
    output = subprocess.check_output(bashCommand, shell=True)
    return output

def main():
    docker_id = get_docker_id()
    docker_id = docker_id.decode()[:-1]
    
    personas = Persona.select().where(Persona.source_ip == docker_id)
    bots = []
    
    for persona in personas:
        print(persona.name)

    for persona in personas:
        bot = Webdriver(persona)
        bot.start()
        bots.append(bot)

    # Wait all the threads to finish
    for bot in bots:
        bot.join()
        
    parse_log(personas)

    print('Program finished successfully')


if __name__ == '__main__':
    main()
