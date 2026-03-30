# 简介
crontab被macos废弃了，替代品是launchd。相对于cron，它多了以下功能：
- 开机执行、睡眠补执行
- 守护进程
- 日志功能

# 配置
## 配置目录
用来存放 定时器任务配置文件的 有5个目录：
- /Library/LaunchDaemons：开机就跑（无需登录），适合服务程序、后台守护进程
- ~/Library/LaunchAgents：用户登陆后跑，适合定时脚本、自动化工具

## 配置文件格式
launchd 不用命令写规则，而是用 XML（plist）配置。每个任务 = 一个 .plist

### 行为控制
```xml
<plist>
  <!-- 开机/加载时执行 -->
  <key>RunAtLoad</key>
  <true/>

  <!-- 保持常驻，程序退出就自动重启 -->
  <key>KeepAlive</key>
  <true/>
    
</plist>
```

### 间隔时间
```xml
<plist>
  <!-- 每天 03:00 执行 -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>3</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>

  <!-- 每 600s 执行一次 -->
  <dict>
    <key>StartInterval</key>
    <integer>600</integer>
  </dict>
</plist>
```

### 配置demo
示例配置的任务每600s执行一次：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.example.test</string>
    <key>ProgramArguments</key>
    <array>
      <string>/Users/you/script.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
  </dict>
</plist>
```

### 日志
```xml
<plist>
  <key>StandardOutPath</key>
  <string>/tmp/myjob.log</string>
  
  <key>StandardErrorPath</key>
  <string>/tmp/myjob.err</string>
</plist>
```

# 使用
加载任务：`launchctl load ~/Library/LaunchAgents/com.example.test.plist`
卸载任务：`launchctl unload ~/Library/LaunchAgents/com.example.test.plist`
查看任务状态：`launchctl list | grep example`