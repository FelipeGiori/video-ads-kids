import subprocess
import schedule
import time

def get_docker_id():
    bashCommand = "head -1 /proc/self/cgroup|cut -d/ -f3"
    output = subprocess.check_output(bashCommand, shell=True)
    return output


def get_time():
    docker_id = get_docker_id()
    docker_id = docker_id.decode()[:-1]

    mg_times = ["9:00", "15:00", "19:00"]
    pb_times = ["11:00", "17:00", "21:00"]

    docker = ["d6f18b0f8e45bebf19f2de53c469cebc429d2f013b896ba3b1f474e9bd43b271",
             "3a7bb8ba7918c766debf1571924f8eb056938606dfb8cd63d05505b7a761772f",
             "3ee141a9362caaaaf0ebaedc2ba3734e2f11fdf385ad8bea1da59aa8e5c59a67",
             "825c4b38ff7c96db7686846cd172ec2a2b566960c7d3627e38ecd2330d0de2ce",
             "0a09016f0d144dcbb1c0891bc80a99ef56d82087a8f4e825a8d68382b092b98d"]

    if(docker_id == docker[0]):
        return pb_times
    elif(docker_id == docker[1]):
        return pb_times
    elif(docker_id == docker[2]):
        return mg_times
    elif(docker_id == docker[3]):
        return mg_times
    elif(docker_id == docker[4]):
        return mg_times
    else:
        print("Docker id não existe")
        return []


def run_bot():
    cmd = "./run.sh"
    subprocess.check_output(cmd, shell=True)


def main():
    sch_time = get_time()

    schedule.every().day.at(sch_time[0]).do(run_bot)
    schedule.every().day.at(sch_time[1]).do(run_bot)
    schedule.every().day.at(sch_time[2]).do(run_bot)

    while True:
        schedule.run_pending()
        time.sleep(2)

if __name__ == "__main__":
    main()