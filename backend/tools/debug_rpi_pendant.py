import backend.pendant_daemon as pendant_daemon


def main():
    controller = pendant_daemon.RPI_GPIO_Device()
    last_state = None
    updates = 0
    while True:
        states = controller.get_state_table()
        if states != last_state:
            updates += 1
            print(f"===== UPDATE [{updates}] =====")
            print(repr(controller))


if __name__ == "__main__":
    main()
