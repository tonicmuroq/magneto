Magneto
=======
部署服务的中心节点, 暂时是单点的.

API
---

*   注册一个新App

        http -f POST http://localhost:8881/app/new name=dalaran version=3e4d5f app_yaml='{"appname":"dalaran", "version":"3d4e5f", "services":["redis", "mysql"]}'
        
    参数:
    
    * name: 项目名称, 一般跟应用名称相同, 不同也没有关系.
    * version: 版本号, 应用对应项目在gitlab仓库里的版本号.
    * app\_yaml: 仓库里的 app.yaml 文件的 json 格式内容.
    * config\_yaml: 仓库里的 config.yaml 文件的 json 格式内容, 可选.
    
*   注册一个新host

        http -f POST http://localhost:8881/host/new host='10.1.201.16' name='fili3'
        
    参数:
    
    * host: 节点的 IP 地址.
    * name: 节点的名字, 可选.
    
*   部署一个应用到指定节点

        http -f POST http://localhost:8881/app/dalaran/3e4d5f/deploy hosts='10.1.201.16' hosts='10.1.201.17'
        
    参数:
    
    * hosts: 节点的 IP 地址, 可以指定多个.
    * url 格式为 /app/\<appname\>/\<appversion\>/deploy, 注意这里是应用名称, 不是项目名称.
    
*   下线指定节点的应用

        http -f POST http://localhost:8881/app/dalaran/3e4d5f/remove hosts='10.1.201.16'
        
    参数:
    
    * hosts: 节点的 IP 地址, 可以指定多个.
    * url 格式为 /app/\<appname\>/\<appversion\>/remove, 同样是应用名称, 不是项目名称.
    
------

应用名和项目名暂时比较乱, 为了方便最好把应用名和项目名统一.
