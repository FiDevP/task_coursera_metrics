import asyncio

metrics_storage = {}


class ClientServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        resp = process_data(data.decode())
        self.transport.write(resp.encode())


def process_data(data):
    msg_ok = 'ok\n\n'
    msg_wrong_command = 'error\nwrong command\n\n'
    msg_index_error = 'Index error'

    if data.strip('\n').strip() == '':
        return msg_wrong_command

    command = data.split()
    if command[0] == 'put':
        if len(command) == 4:
            try:
                key, value, timestamp = command[1], float(command[2]), int(command[3])
            except ValueError:
                return msg_wrong_command
            old_metrics_list = metrics_storage.get(key, [])
            for i, metric in enumerate(old_metrics_list):
                if metric[0] == timestamp:
                    old_metrics_list.remove((timestamp, metric[1]))
                    old_metrics_list.insert(i, (timestamp, value))
                    return msg_ok

            old_metrics_list.append((timestamp, value))
            metrics_storage.update({key: old_metrics_list})
            return msg_ok
        else:
            return msg_wrong_command

    elif command[0] == 'get':
        if len(command) == 2:
            send_metrics = 'ok\n'
            key = command[1]
            if key == '*':
                for key, value in metrics_storage.items():
                    for i in value:
                        timestamp_from_dict = i[0]
                        value_from_dict = i[1]
                        try:
                            send_metrics += f'{key} {value_from_dict} {timestamp_from_dict}\n'
                        except IndexError:
                            return msg_index_error
                return send_metrics + '\n'

            metrics = metrics_storage.get(key, None)
            if metrics is None:
                return msg_ok
            try:
                for metric in metrics:
                    send_metrics += f'{key} {metric[1]} {metric[0]}\n'
                return send_metrics + '\n'
            except IndexError:
                return msg_index_error

        else:
            return msg_wrong_command

    else:
        return msg_wrong_command


def run_server(host, port):
    loop = asyncio.get_event_loop()
    coro = loop.create_server(ClientServerProtocol, host, port)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    run_server('127.0.0.1', 8888)