import os
import asyncio

async def run_moder():
    os.system('run_moder.py')


async def run_command():
    os.system('run_command.py')


if __name__ == '__main__':
    asyncio.run(run_moder())
    asyncio.run(run_command())
