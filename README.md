## Install
基于mitmproxy稳定版本5.2，python3.8
其他版本可能会出现中文解码失败的情况

`pip install mitmproxy-lin-customization`
``

## 修改内容
### 修改mitmproxy源码以加入接口响应时间的排序
实际测试中需要查看接口的响应时间看看是否时间很长，mitmproxy的原生时间排序是根据
发送时间进行排序
这里加入接口花费时间

![img.png](img_3.png)

### 自动修改参数跑多个接口的插件

实际测试中有许多bug是需要一定的数据量发现的，并且有时需要造大量的重复数据，对人力比较浪费 根据这个需求写一个插件来自动根据接口发送接口

详情见AutoReplayFlows
`replay.auto_replay flows path nums`

- flows:指定哪些接口重跑，一般为 @focus
- path:选择要递增的参数的路径
- nums:要重新跑的接口的数量,默认为5

`replay.auto_replay @focus input.account 10`

为了配合这个插件使用，修改mitmproxy的快捷键 将`R`映射到`replay.auto_replay @focus`

mitmproxy/tools/console/defaultkeys.py 加上一行

```python
km.add("R", "console.command replay.auto_replay @focus", ["global"], "Set intercept")
```

### graphql-view

针对graphql加入两种view

![img_1.png](img_1.png)

![img.png](img_2.png)

