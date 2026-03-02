PYTHON ?= python3
PIP    ?= pip3

.PHONY: install run clean

install:
	$(PIP) install -r requirements.txt

run:
	@test -n "$(contact)" || { echo "用法: make run contact=文件传输助手 message=hello"; exit 1; }
	@test -n "$(message)" || { echo "用法: make run contact=文件传输助手 message=hello"; exit 1; }
	$(PYTHON) agent.py -contact "$(contact)" -message "$(message)"

clean:
	rm -f /tmp/wechat_agent.png /tmp/wechat_agent_1x.png
	find . -type d -name __pycache__ -exec rm -rf {} +
