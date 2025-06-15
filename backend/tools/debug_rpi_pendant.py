import backend.pendant_daemon as pendant_daemon
import backend.includes_python.service_helper as service_helper


def main():
    controller = pendant_daemon.RPI_GPIO_Device()
    last_state = None
    updates = 0
    while not service_helper.time_to_stop():
        states = controller.get_state_table()
        if states != last_state:
            updates += 1
            print(f"===== UPDATE [{updates}] =====")
            print(repr(states))
        last_state = states


if __name__ == "__main__":
    main()
