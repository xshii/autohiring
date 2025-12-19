# AutoHiring 使用用例

## 1. 电话归属地查询

### 用例 1.1: 查询单个号码
```bash
autohiring phone lookup 13800138000
```
输出：
```
        电话号码信息
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ 属性     ┃ 值            ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 号码     │ 138 0013 8000 │
│ 归属地   │ 北京市        │
└──────────┴───────────────┘
```

### 用例 1.2: 批量查询 CSV
输入文件 `candidates.csv`:
```csv
姓名,电话,职位
张三,13800138000,Java开发
李四,13912345678,前端开发
```

命令：
```bash
autohiring phone csv candidates.csv -c 电话
```

输出文件 `candidates.csv`:
```csv
姓名,电话,归属地,职位
张三,13800138000,北京市,Java开发
李四,13912345678,江苏省常州市,前端开发
```

---

## 2. 网页爬取（Chrome 插件配合）

### 用例 2.1: 爬取 Boss 直聘候选人列表

**步骤：**
1. 启动爬虫服务
   ```bash
   autohiring scraper start
   ```

2. 打开 Chrome，安装插件，进入 Boss 直聘

3. 插件自动识别候选人卡片，点击"开始爬取"

4. 插件模拟点击每个候选人，提取信息：
   - 姓名
   - 电话
   - 期望薪资
   - 工作经验
   - 学历

5. 数据自动发送到本地服务，CLI 显示：
   ```
   ✓ 收到数据: 张三
   ✓ 收到数据: 李四
   ✓ 收到数据: 王五
   ```

6. 导出数据
   ```bash
   autohiring scraper export -o candidates.json
   ```

---

## 3. 网络电话

### 用例 3.1: 拨打单个电话
```bash
autohiring voip call 13800138000
```

### 用例 3.2: 批量外呼
```bash
autohiring voip batch numbers.txt --interval 10
```

### 用例 3.3: 查看配置
```bash
autohiring voip config
```
输出：
```
        阿里云语音配置
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ 环境变量                  ┃ 值        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ ALIYUN_ACCESS_KEY_ID      │ ***       │
│ ALIYUN_ACCESS_KEY_SECRET  │ ***       │
│ ALIYUN_VOICE_SHOW_NUMBER  │ [未设置]  │
│ ALIYUN_VOICE_TTS_CODE     │ [未设置]  │
└───────────────────────────┴───────────┘
```

---

## 4. TTS 语音合成

### 用例 4.1: 生成语音文件
```bash
autohiring tts generate "您好，这里是招聘团队" -o hello.mp3
```

### 用例 4.2: 使用话术模板
```bash
autohiring tts template initial_contact \
  --company "ABC科技" \
  --platform "Boss直聘" \
  --position "Java开发" \
  -o intro.mp3
```

### 用例 4.3: 列出可用语音
```bash
autohiring tts voices
```

---

## 5. 交互式 Shell

```bash
autohiring shell
```

输出：
```
AutoHiring 交互式命令行
输入命令（如: phone lookup 13800138000），输入 exit 退出

autohiring: phone lookup 13800138000
        电话号码信息
...
autohiring: version
autohiring v0.1.0
autohiring: exit
再见！
```

---

## 典型工作流程

```
1. 启动爬虫服务
   autohiring scraper start

2. Chrome 插件爬取候选人 → 数据自动同步

3. 导出数据
   autohiring scraper export -o candidates.csv

4. 添加归属地信息
   autohiring phone csv candidates.csv -c 电话

5. 批量外呼（意愿调查）
   autohiring voip batch candidates.csv --template survey
```
