# Phase 5a.0 证据 — 探针闸门

- 生成时间：2026-09-11T17:32:49+08:00
- 分支：simple-agent @ 11e9f8b

## 1. vendor 锁版本

```
$ git -C .agent/vendor/tau-bench log -1 --format="%H %ci %s"
59a200c6d575d595120f1cb70fea53cef0632f6b 2026-03-18 10:36:06 -0700 Merge pull request #80 from sierra-research/update-readme-tau3-bench
```

## 2. sidecar venv（独立环境，完整安装）

```
$ .agent/venv/tau/bin/python --version
Python 3.10.21
$ .agent/venv/tau/bin/pip list | wc -l
95
$ grep -iE "litellm|openai|pydantic|tau" (sidecar venv)
litellm==1.61.20
openai==2.54.0
pydantic==2.13.5
tau_bench==0.1.0
# 注：litellm 1.100.1 在 Python 3.10 报 ImportError(typing.NotRequired)，已 pin 1.61.20
```

### sidecar venv 完整 pip list

```
Jinja2==3.1.6
MarkupSafe==3.0.3
PyYAML==6.0.3
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
annotated-types==0.8.0
anthropic==1.4.0
anyio==4.15.1
async-timeout==5.0.1
attrs==26.1.0
boto3==1.43.91
botocore==1.43.91
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.1
click==8.5.0
cryptography==50.0.1
distro==1.9.0
docstring_parser==0.18.0
eval_type_backport==0.4.0
exceptiongroup==1.3.1
fastuuid==0.14.0
filelock==3.32.6
frozenlist==1.8.0
fsspec==2026.7.0
google-ai-generativelanguage==0.6.15
google-api-core==2.33.0
google-api-python-client==2.200.0
google-auth-httplib2==0.4.2
google-auth==2.58.0
google-generativeai==0.8.6
googleapis-common-protos==1.75.0
grpcio-status==1.71.2
grpcio==1.83.1
h11==0.16.0
hf-xet==1.6.0
httpcore2==2.12.0
httpcore==1.0.9
httplib2==0.32.0
httpx2==2.12.0
httpx==0.28.1
huggingface_hub==1.31.0
idna==3.19
importlib_metadata==8.9.0
jiter==0.16.0
jmespath==1.1.0
jsonpath-python==1.1.6
jsonschema-specifications==2025.9.1
jsonschema==4.26.0
litellm==1.61.20
mistralai==2.10.0
multidict==6.8.0
numpy==2.2.6
openai==2.54.0
opentelemetry-api==1.44.0
opentelemetry-semantic-conventions==0.65b0
packaging==26.3
pip==26.2.1
propcache==0.5.2
proto-plus==1.28.2
protobuf==5.29.6
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==3.0
pydantic-settings==2.15.0
pydantic==2.13.5
pydantic_core==2.46.5
pyparsing==3.3.2
python-dateutil==2.9.0.post0
python-dotenv==1.2.3
referencing==0.37.0
regex==2026.9.3
requests==2.34.2
rpds-py==0.30.0
s3transfer==0.19.2
setuptools==84.0.0
six==1.17.0
sniffio==1.3.1
tau_bench==0.1.0
tenacity==9.1.4
termcolor==3.3.0
tiktoken==0.14.0
tokenizers==0.23.2
tqdm==4.70.0
truststore==0.10.4
typing-inspection==0.4.4
typing_extensions==4.16.0
uritemplate==4.2.0
urllib3==2.7.0
wheel==0.48.0
yarl==1.24.5
zipp==4.1.0
```

## 3. 隔离证明：mini-agent 环境 pip list 前后 diff 为空

```
$ diff <(pip list BEFORE) <(pip list AFTER)
[diff empty]
$ grep -iE "torch|transformers" (mini-agent)
(none)
```

## 4. replay 成本探测：StubUser 注桩后 replay LLM 调用 = 0

```
$ .agent/venv/tau/bin/python (patch tau_bench.envs.user.completion -> counter; rpc_reward)
reward with StubUser: 0.0 | LLM calls during replay: 0
GT actions count: 1 | GT respond actions: 0
replay with QueueUser: no raise (no respond GT action)
LLM calls total after all: 0
```

## 5. sidecar 全回路（HTTP JSON-RPC，session_id 流转）

```
$ bash scripts/tau_sidecar.sh start
[tau] started pid=203659 host=127.0.0.1 port=8010
$ cat .agent/tau_pidmap.json
{"service":"tau-sidecar","host":"127.0.0.1","port":8010,"pid":203845,"started_at":"2026-09-11T17:32:21+08:00"}
$ ss -tlnp | grep :8010
LISTEN 0      5          127.0.0.1:8010      0.0.0.0:*    users:(("python",pid=203845,fd=3))  
$ POST reset {env_name:retail, task_id:2}
{"result":{"session_id":"32d2afd7-...","env_name":"retail","task_id":2}}
$ POST list_tools -> 16 tools: [calculate, cancel_pending_order, ...]
$ POST get_wiki -> wiki_len: 5718
$ POST get_instruction -> "You are Yusuf Rossi in 19122. You want to know how many tshirt options..."
$ POST step {action: respond} -> {"status":"WAITING_FOR_USER"}
$ POST provide_user_msg -> {"ok":true}
$ POST reward -> {"reward":0.0,"info":{"r_outputs":0.0,"outputs":{"10":false}}}
```

## 6. 接口缺口验证（v1.4 §2.5）

```
two sessions distinct: True
terminate step: {'observation': 'Transfer successful', 'done': True, 'reward': 0.0}
health sessions: {'status': 'ok', 'sessions': 2}
health after end A: {'status': 'ok', 'sessions': 1}
B instruction non-empty: True
# => transfer_to_human_agents done=True ✅ | get_wiki 非空 ✅ | session 隔离/注销 ✅
```

## 7. driver 侧自写 user simulator（DeepSeek openai 兼容，跑通一轮）

```
$ python3 /tmp/tau_probe_driver.py
instruction: Your user id is mia_li_3668. You want to fly from New York to Seattle on May 20 (one way). You do not want to fly before 11am est. You want to fly in economy. You prefer direct flights but one stopover also fine. If there are multiple options, you prefer the one with the lowest price. You have 3 baggages. You do not want insurance. You want to use your two certificates to pay. If only one certificate can be used, you prefer using the larger one, and pay the rest with your 7447 card. You are reactive to the agent and will not say anything that is not asked. Your birthday is in your user profile so you do not prefer to provide it.
wiki_len: 6155
first user message: "I'd like to book a one-way flight from New York to Seattle on May 20."
usage: 304 tokens
```

## 8. 已知地雷覆盖（v1.3 三条）

- 非阻塞哨兵：step respond 返回 WAITING_FOR_USER，无死锁 ✅
- RESPOND 语义：无 tool_call 的纯文本 = respond，由 driver 续聊（5a.1 落地）
- turn 0：真实首轮消息由 driver 用 hidden instruction 生成（见 §7），hidden instruction 不进 worker 对话历史
