# Windows / PowerShell 调用要点（实测）

Windows 环境调用 open API 的已知坑与解法。类 Unix 环境可忽略本文。

## curl 别名坑

- PowerShell 的 `curl` 是 `Invoke-WebRequest` 别名，`-s`/`-H` 参数会报错（如"缺少参数 SessionVariable"）。**必须用 `curl.exe` 全名调用**
- 丢弃输出用 `NUL` 而非 `/dev/null`：`curl.exe -s -o NUL -w "%{http_code}" ...`

## 服务器可达性检查（Windows 版）

```powershell
curl.exe -s -o NUL -w "%{http_code}" -H "X-API-Key: invalid" "https://m.imzhuge.com/startactivity/api/open/my_balance/?activity_id=1"
# 期望 401（服务可达且鉴权生效）；连接失败则服务不可达
```

## 中文 JSON 请求体：禁止命令行内联

内联 `-d "..."` 会因编码损坏返回 `"请求体不是合法的JSON"`。正确做法：

1. 用 write 工具把 payload 写入 UTF-8（无 BOM）临时文件
2. **文件名带时间戳**（如 `%TEMP%\opencode\trade_payload_20261105_1541.json`），防止写入失败时误用上一次的陈旧文件
3. 用 `--data-binary "@文件"` 发送

```powershell
# PowerShell 无 bash 风格的 ${VAR:-default} 语法，默认值需显式判断（或直接写完整 URL）
$base = if ($env:IMZHUGE_BASE_URL) { $env:IMZHUGE_BASE_URL } else { 'https://m.imzhuge.com' }
curl.exe -s -X POST -H "X-API-Key: $env:IMZHUGE_API_KEY" `
  -H "Content-Type: application/json" `
  --data-binary "@C:\Users\...\trade_payload_20261105_1541.json" `
  "$base/startactivity/api/open/trade_confirm/"
```

## 控制台编码

- 读取中文响应前先执行 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`，否则默认编码可能乱码
- 首选 `scripts/trade_demo.py`（进程内自动处理 UTF-8 编码、含下单确认），避开上述大部分坑
