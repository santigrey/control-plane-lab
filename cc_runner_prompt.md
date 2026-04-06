SSH to CiscoKid (192.168.1.10, user jes). Run: python3 /home/jes/control-plane/task_runner.py list

For each approved task, read the payload with: python3 /home/jes/control-plane/task_runner.py get TASK_ID

Execute the instructions in the payload. When done, mark complete with: python3 /home/jes/control-plane/task_runner.py complete TASK_ID "result summary"

If a task fails, mark it with: python3 /home/jes/control-plane/task_runner.py fail TASK_ID "reason"
