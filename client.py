import socket
import time


class ClientError(Exception):
    """
        Пользовательское исключение. Вызывается при неудачном использовании метода put и get.
    """
    def __init__(self, message):
        super(ClientError, self).__init__(message)


class Client:

    def __init__(self, host, port, timeout=None):
        self._host = host
        self._port = port
        self._timeout = timeout

        self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)

    def put(self, name, value, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())

        request = "put {0} {1} {2}\n".format(name, value, timestamp) # формируем запрос
        request_bytes = request.encode('utf-8') # переводим в байты
        try:
            self._sock.send(request_bytes) # отправляем запрос на сервер
            data = self._sock.recv(1024)
            response_raw = data.decode('utf-8')
            response = response_raw.split()
            if response[0] != 'ok':
                raise ClientError("Некорректные данные в ответе сервера")
        except ClientError:
            raise ClientError("Некорректные данные в ответе сервера")

    def get(self, name):
        try:
            request = f"get {name}\n"
            # отправим названием метрики по которой хотим получить данные
            self._sock.send(request.encode('utf-8'))
            # прочтем ответ сервера
            data = self._sock.recv(1024)
            response_raw = data.decode('utf-8')
            # пропарсим ответ сервера и сформируем словарь
            response = response_raw.split('\n')
            response1 = response.copy()
            response1.pop(0)
            # проверим ответ "ок" или "error"
            if response[0] != 'ok':
                raise ClientError("Некорректный ответ сервера")
            elif 'ok' in response1:
                raise ClientError("Некорректный ответ сервера")
            else:
                # проверяем, если ответ просто "ок", отправляем пустой словарь, иначе обрабатывем данные.
                if len(response) == 3:
                    return {}
                else:
                    response_dict = dict()
                    for i_raw in response:
                        if i_raw not in ['', 'ok', 'error']:
                            i = i_raw.split()
                            # проверим что после статуса ответа, данные корректны
                            if len(i) != 3:
                                raise ClientError("Некорректные данные в ответе сервера")
                            else:
                                try:
                                    name_metrics = str(i[0])
                                    value = float(i[1])
                                    timestamp = int(i[2])
                                    list_result = [(timestamp, value)]
                                    k = response_dict.get(name_metrics, 0)
                                    if k == 0:
                                        response_dict[name_metrics] = list_result
                                    else:
                                        response_dict[name_metrics] += list_result
                                except ValueError:
                                    raise ClientError
                    # отсортируем значения в словаре по timestamp
                    for key, value in response_dict.items():
                        value.sort(key=lambda x: x[0])
                    return response_dict

        except Exception as err:
            raise ClientError(err)

    def close(self):
        try:
            self._sock.close()
        except socket.error as err:
            raise ClientError("Error. Do not close the connection", err)


client1 = Client("127.0.0.1", 8888, timeout=15)
client2 = Client("127.0.0.1", 8888, timeout=15)
client1.put("multivalue_key", 12.0)
client2.put("multivalue_key", 12.0, timestamp=1503319741)
client1.put("multivalue_key", 12.0, timestamp=1503319740)
client2.put("multivalue_key", 12.0)
client2.put("multivalue_key", 12.0, timestamp=1503319740)
print(client1.get("multivalue_key"))