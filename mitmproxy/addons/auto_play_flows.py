import json
import queue
import typing

from mitmproxy import command, flow, ctx, http
from mitmproxy.addons.clientplayback import RequestReplayThread


class ChangeParamsByPath:
    @classmethod
    def _handle_path(cls, path: str):
        if path.endswith("]"):
            index = 0
            while path[index] != "[":
                index += 1
            return path[0:index], path[index + 1:-1] if path[index + 1:-1] == "*" else int(path[index + 1:-1])
        else:
            return path, None

    @classmethod
    def _change_value(cls, value: str):
        if not isinstance(value, str):
            value = str(value)

        if value.isdigit():  # 如果是数字就不用计算
            if len(value) == 10:  # 判断为时间戳
                return int(value) + 3600 * 24  # 秒级时间戳
            elif len(value) == 13:
                return int(value) + 3600 * 24 * 1000  # 毫秒秒级时间戳
            else:
                return str(int(value) + 1)  # 普通数字
        l_ = len(value) - 1
        while value[l_].isdigit() and l_ >= 0:  # 拿到数字后缀
            l_ -= 1
        front = value[:l_ + 1]
        back = value[l_ + 1:] or 1  # 可能不存在数字后缀，那么默认从0开始
        return front + str(int(back) + 1)

    @classmethod
    def _change(cls, obj: dict, paths: typing.List[str]):
        path, index = cls._handle_path(paths[0])
        if len(paths) == 1 and obj.get(path, "EOF") != "EOF":  # 迭代终止条件,目标值可能为None，所以自己定义一个值
            if index is None:
                obj[path] = cls._change_value(obj[path])
        else:
            if obj.get(path, "EOF") != "EOF":
                new_obj = obj.get(path)
                cls._change(new_obj, paths[1:])
            else:
                for key, new_obj in obj.items():
                    if isinstance(new_obj, list):
                        for i in new_obj:
                            cls._change(i, paths)
                    elif isinstance(new_obj, dict):
                        cls._change(new_obj, paths)

    @classmethod
    def change(cls, obj: dict, path: str):
        """
        :param obj: 要修改的对象
        :param path: 修改的path，将符合条件第一个path自动增加
            （1）正常path，'name',
            （2）部分相对path 'input.name'
            （3）批量修改列表中的path 'input.hlist[*].name'
        :return:
        """
        paths = path.split(".")
        return cls._change(obj, paths)


class AutoPlayFlows:
    def __init__(self):
        self.q = queue.Queue()
        self.thread: RequestReplayThread = None

    def running(self):
        self.thread = RequestReplayThread(
            ctx.options,
            ctx.master.channel,
            self.q,
        )
        self.thread.start()

    @command.command("replay.auto_replay")
    def start_replay(self, flows: typing.Sequence[flow.Flow], path: str, nums: int = 5) -> None:
        lst = []
        paths = path.split(";")
        for f in flows:
            hf = typing.cast(http.HTTPFlow, f)
            for i in range(nums):
                hf = hf.copy()
                # Prepare the flow for replay
                hf.backup()
                hf.request.is_replay = True
                hf.response = None
                hf.error = None
                # https://github.com/mitmproxy/mitmproxy/issues/2197
                if hf.request.http_version == "HTTP/2.0":
                    hf.request.http_version = "HTTP/1.1"
                    host = hf.request.headers.pop(":authority", None)
                    if host is not None:
                        hf.request.headers.insert(0, "host", host)
                # replay auto nums
                data_ = json.loads(hf.request.text)
                for j in paths:
                    ChangeParamsByPath.change(data_, j)
                # ctx.log(data_)
                hf.request.text = json.dumps(data_)
                lst.append(hf)
                self.q.put(hf)

        ctx.master.addons.trigger("update", lst)


