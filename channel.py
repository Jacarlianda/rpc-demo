# coding=utf-8

import socket
import threading
import uuid
import datetime
import logging.config


# -------短连接--------
class NetServerChannel:
    def __init__(self):
        pass

    def listen(self, ip, port, count):
        try:
            self.ip = ip
            self.port = port

            self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.m_socket.bind((ip, port))

            self.m_socket.listen(count)

            args_param = []
            args_param.append(1800000)

            kwargs_param = {}
            kwargs_param.__setitem__('HZRY', '42000')
            kwargs_param.__setitem__('SHXX', '3600000')

            thd = threading.Thread(target=self.__work, name='ListenThread', args=args_param, kwargs=kwargs_param)
            thd.setDaemon(True)
            thd.start()
        except Exception as exception:
            print exception
        finally:
            pass

    def __work(self, *args, **kwargs):
        self.checkLabel = True

        while self.checkLabel:
            channel, addr_port = self.m_socket.accept()
            chat = ChatServer(channel, addr_port)

    def addEventHandler(self, function):
        NetServerChannel.function = function

    def removeEventHandler(self):
        if NetServerChannel.function != None:
            NetServerChannel.function = None

    def sendRec(self, arg):
        chat = ChatServer.selectItem(arg.id)

        channel = chat.channel

        if channel != None:
            len_data = len(arg.response_data)

            len_str = self.__Int2String(len_data)

            data = len_str + arg.response_data

            channel.send(data)

    def __Int2String(self, count):
        str = '%04d' % count
        return str


class NetClientChannel:
    def __init__(self, ip, port):
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port

    def __connection(self):
        self.m_socket.connect((self.ip, self.port))

    def __close(self):
        try:
            self.m_socket.close()
        except Exception as exception:
            pass
        finally:
            pass

    def send(self, data):
        result = ''

        try:
            self.__connection()

            count = len(data)

            len_str = self.__Int2String(count)

            send_data = len_str + data

            self.m_socket.send(send_data)

            recvcountstr = self.m_socket.recv(4)

            recvcount = int(recvcountstr)

            shengyu_count = recvcount

            recv_data = ''

            check = True

            while check:
                temp_str = self.m_socket.recv(shengyu_count)

                recv_data += temp_str

                temp_count = len(temp_str)

                shengyu_count = shengyu_count - temp_count

                if shengyu_count == 0:
                    check = False

            result = recv_data

            self.__close()

            pass
        except Exception as exception:
            print exception
        finally:
            return result

    def __Int2String(self, count):
        str = '%04d' % count

        return str


class ChatServer:
    __Map = None

    state = 0

    __gc_thread = None

    channel = object()

    def __init__(self, channel, addr_port):
        self.ip = addr_port[0]
        self.port = addr_port[1]
        self.channel = channel
        self.id = str(uuid.uuid1())
        self.__checkReceive = True
        self.initTime = datetime.datetime.now()

        if ChatServer.__Map == None:
            ChatServer.__Map = {}

        tkey = ChatServer.__Map.has_key(self.id)

        lok = threading.Lock()

        if tkey == False:
            lok.acquire()
            ChatServer.__Map[self.id] = self
            lok.release()

        self.state = 1

        self.is_error = False

        if ChatServer.__gc_thread == None:
            ChatServer.__gc_thread = threading.Thread(target=self.__gc_work, name="gc")
            ChatServer.__gc_thread.setDaemon(True)
            ChatServer.__gc_thread.start()

        thd = threading.Thread(target=self.__ReceiveMessage, name="ChatReceive")
        thd.setDaemon(True)
        thd.start()

    def __gc_work(self):
        threading._sleep(30)

        lok = threading.Lock()

        while True:
            values = ChatServer.__Map.values()

            datetime_now = datetime.datetime.now()

            del_objs = list()

            del_check = False

            for temp in values:
                if temp.state == 0:
                    del_objs.append(temp)

                    del_check = True
                else:
                    timespan = datetime_now - temp.initTime

                    xiangcha_second = timespan.total_seconds()

                    xiangcha_int = int(xiangcha_second)

                    if xiangcha_int > 600:
                        del_objs.append(temp)
                        del_check = True

            if del_check == True:
                for tmp in del_objs:
                    lok.acquire()
                    tmp.close()
                    ChatServer.__Map.__delitem__(tmp.id)
                    lok.release()

            threading._sleep(10)

        pass

    def __ReceiveMessage(self):
        temp_error_obj = None

        while self.__checkReceive:
            try:
                len_str = self.channel.recv(4)
                len_int = int(len_str)

                temp_check = True

                shengyu_count = len_int

                recv_data = ''

                while temp_check:
                    temp_str = self.channel.recv(shengyu_count)

                    recv_data += temp_str

                    tmp_count = len(temp_str)

                    shengyu_count = shengyu_count - tmp_count

                    if shengyu_count == 0:
                        temp_check = False

            except socket.error as exception:
                self.state = 0
                temp_error_obj = exception
            except Exception as exception:
                self.state = 0
                temp_error_obj = exception
            finally:
                eventArgs = EventArgs(self.id, recv_data)

                if self.state == 0:
                    self.close()
                    self.is_error = True
                    eventArgs.is_error = True
                    eventArgs.error_obj = temp_error_obj

                args = []
                args.append(eventArgs)

                self.fireEvent(args)

    def fireEvent(self, args):
        try:
            temp = args[0]

            if NetServerChannel.function != None:
                NetServerChannel.function(temp)
        except Exception as exception:
            pass
        finally:
            pass

    def close(self):
        try:
            self.channel.close()
        except Exception as exception:
            pass
        finally:
            self.__checkReceive = False
            self.state = 0

    @staticmethod
    def selectItem(id):
        result_channel = None

        tkey = ChatServer.__Map.has_key(id)

        if tkey == True:
            result_channel = ChatServer.__Map[id]

        return result_channel


class EventArgs:
    def __init__(self, id, data):
        self.id = id
        self.request_data = data
        self.response_data = None
        self.is_error = False
        self.error_obj = None


# ------订阅/发布 长连接-------
# 发布者
class PublisherObject:
    def __init__(self):
        pass

    def listen(self, ip, port, count):
        try:
            self.ip = ip
            self.port = port

            self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.m_socket.bind((ip, port))

            self.m_socket.listen(count)

            args_param = []
            args_param.append(28880000)

            kwargs_param = {}
            kwargs_param.__setitem__('shxx', 11000)

            thd = threading.Thread(target=self.__work, name='ListenThread', args=args_param, kwargs=kwargs_param)
            thd.setDaemon(True)
            thd.start()
        except Exception as exception:
            pass
        finally:
            pass

    def __work(self, *args, **kwargs):
        self.checkLabel = True

        while self.checkLabel:
            channel, addr_port = self.m_socket.accept()

            chat = ChatObject(channel, addr_port)

    def addEventHandler(self, function):
        PublisherObject.function = function

    def removeEventHandler(self, function):
        if PublisherObject.function != None:
            PublisherObject.function = None

    def send(self, sid, data):
        chat = ChatObject.selectItem(sid)

        channel = chat.channel

        if channel != None:
            len_data = len(data)

            len_str = self.__Int2String(len_data)

            msg = len_str + data

            channel.send(msg)

    def release(self, sid):
        chat = ChatObject.deleteItem(sid)

        pass

    def __Int2String(self, count):
        str = '%04d' % count

        return str


class ChatObject:
    __Map = {}

    state = 0

    __gc_thread = None

    def __init__(self, channel, addr_port):
        self.id = str(uuid.uuid1())

        self.ip = addr_port[0]
        self.port = addr_port[1]

        self.channel = channel

        self.__checkReceive = True

        self.initTime = datetime.datetime.now()

        if ChatObject.__Map == None:
            ChatObject.__Map = {}

        tkey = ChatObject.__Map.has_key(self.id)

        lok = threading.Lock()

        if tkey == False:
            lok.acquire()
            ChatObject.__Map[self.id] = self
            lok.release()

        self.state = 1

        self.is_error = False

        thd = threading.Thread(target=self.__ReceiveMessage, name='Chat')
        thd.setDaemon(True)
        thd.start()

    def __ReceiveMessage(self):
        temp_error_obj = None

        while self.__checkReceive:
            recv_data = ''

            try:
                len_str = self.channel.recv(4)

                len_int = int(len_str)

                temp_check = True

                shengyu_count = len_int

                while temp_check:
                    temp_str = self.channel.recv(shengyu_count)

                    recv_data += temp_str

                    tmp_count = len(temp_str)

                    shengyu_count = shengyu_count - tmp_count

                    if shengyu_count == 0:
                        temp_check = False

            except Exception as exception:
                self.state = 0
                temp_error_obj = exception
                logger.error(str(exception) + str(": Network Error Device Disconnect"))
            finally:
                eventObj = EventObject(self.id, recv_data)

                if self.state == 0:
                    self.is_error = True
                    self.close()
                    eventObj.is_error = self.is_error
                    eventObj.error_obj = temp_error_obj

                args_param = []
                args_param.append(eventObj)

                kwargs_param = {}
                kwargs_param.__setitem__('njxx', 3000)
                kwargs_param.__setitem__('njxx', 8664000)

                thd = threading.Thread(target=self.fireEvent, name='fire_Thread', args=args_param, kwargs=kwargs_param)
                thd.setDaemon(True)
                thd.start()

        pass

    def fireEvent(self, *args, **kwargs):
        temp = args[0]

        if PublisherObject.function != None:
            PublisherObject.function(temp)

    @staticmethod
    def selectItem(id):
        result_channel = None

        tkey = ChatObject.__Map.has_key(id)

        if tkey == True:
            result_channel = ChatObject.__Map[id]

        return result_channel

    @staticmethod
    def get_all_Items():
        lstItems = []
        lstItems = ChatObject.__Map.values()
        return lstItems

    @staticmethod
    def deleteItem(id):
        tkey = ChatObject.__Map.has_key(id)

        if tkey == True:
            lok = threading.Lock()
            lok.acquire()
            ChatObject.__Map.__delitem__(id)
            lok.release()
        pass

    def close(self):
        try:
            self.channel.close()
        except Exception as exception:
            pass
        finally:
            self.__checkReceive = False
            self.state = 0


class EventObject:
    def __init__(self, id, data):
        self.id = id
        self.data = data
        self.is_error = False
        self.error_obj = None


# 订阅者
class SubscriberObject:
    def __init__(self):
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connection(self, ip, port):
        self.ip = ip
        self.port = port

        self.__checkLabel = True

        try:
            self.m_socket.connect((ip, port))

            self.state = 1
        except Exception as exception:
            self.state = 0
        finally:
            pass

    def close(self):
        try:
            self.__checkLabel = False
            self.state = 0

            self.m_socket.close()
        except Exception as exception:
            pass
        finally:
            pass

    def addEventHandler(self, function):
        SubscriberObject.function = function

    def removeEventHandler(self):
        SubscriberObject.function = None

    def asyncReceive(self):
        thd = threading.Thread(target=self.__work, name='Chat')
        thd.setDaemon(True)
        thd.start()

    def __work(self):
        temp_error_obj = None

        while self.__checkLabel:
            recv_data = ''
            try:
                len_str = self.m_socket.recv(4)

                len_int = int(len_str)

                temp_check = True

                shengyu_count = len_int

                while temp_check:
                    temp_str = self.m_socket.recv(shengyu_count)

                    recv_data += temp_str

                    tmp_count = len(temp_str)

                    shengyu_count = shengyu_count - tmp_count

                    if shengyu_count == 0:
                        temp_check = False

            except Exception as exception:
                self.state = 0
                temp_error_obj = exception
            finally:
                eventObj = EventObject("", recv_data)

                if self.state == 0:
                    self.is_error = True
                    self.close()
                    eventObj.is_error = self.is_error
                    eventObj.error_obj = temp_error_obj

                args_param = []
                args_param.append(eventObj)

                kwargs_param = {}
                kwargs_param.__setitem__('njxx', 3000)
                kwargs_param.__setitem__('njxx', 8664000)

                thd = threading.Thread(target=self.fireEvent, name='fire_Thread', args=args_param, kwargs=kwargs_param)
                thd.setDaemon(True)
                thd.start()

        pass

    def fireEvent(self, *args, **kwargs):
        temp = args[0]

        if SubscriberObject.function != None:
            SubscriberObject.function(temp)

    def send(self, data):

        if self.state == 0:
            pass
        else:
            count = len(data)

            len_str = self.__Int2String(count)

            send_data = len_str + data

            self.m_socket.send(send_data)

    def __Int2String(self, count):
        str = '%04d' % count

        return str
