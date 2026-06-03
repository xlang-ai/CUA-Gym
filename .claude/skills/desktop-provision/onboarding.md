# First-Time Aliyun Setup

Complete these steps when `discover_and_fill.py` reports **missing AccessKey** or **no matching image**.

---

## Create AccessKey

Required before any script can call Aliyun APIs. **Never paste keys in chat** — only store in local `.env`.

### Recommended: RAM sub-user (not root account)

1. Sign in to [Alibaba Cloud Console](https://home.console.aliyun.com/)
2. Open **RAM → AccessKey**: [https://ram.console.aliyun.com/manage/ak](https://ram.console.aliyun.com/manage/ak)
3. **Users → Create User** → enable **OpenAPI AccessKey**
4. **Attach permissions** (pick one):
   - Simple: `AliyunECSFullAccess`
   - Tighter: custom policy with `ecs:*` and `vpc:Describe*`
5. Create AccessKey → save **AccessKey ID** and **AccessKey Secret** (secret shown once)
6. At repo root: `cp .env.example .env`
7. Edit `.env`:
   ```bash
   ALIYUN_ACCESS_KEY_ID=LTAI...
   ALIYUN_ACCESS_KEY_SECRET=...
   DESKTOP_SSH_PASSWORD=...   # root password from OSWorld image build
   ALIYUN_USE_PRIVATE_IP=0    # Mac / local dev (public IP)
   ```
8. Ensure PostPaid ECS is allowed and account has balance

### Root account AccessKey (not recommended)

Console → profile → **AccessKey Management**. Same `.env` fields. Prefer RAM.

---

## Install dependencies

### Aliyun Python SDK

```bash
pip install alibabacloud_ecs20140526 alibabacloud_tea_openapi alibabacloud_vpc20160428
```

Or: `python scripts/preflight.py --install-deps` (after user confirms).

### sshpass (Mac / verify + harness SSH tunnel)

```bash
# macOS
brew install sshpass

# Debian/Ubuntu
sudo apt install sshpass
```

`preflight.py` checks for `sshpass`.

---

## Import OSWorld Desktop image

1. Download qcow2 from [HuggingFace ubuntu_osworld](https://huggingface.co/datasets/xlangai/ubuntu_osworld)
2. ECS console → **自定义镜像** → import qcow2
3. Name should contain `osworld` or `cua-gym`
4. Note the **region**

---

## VPC & network (same region as image)

- One **VPC** + **vSwitch**
- **Security group** inbound: TCP **22**, TCP **5000**

---

## Run the skill

At repo root, fill `.env` (see above). Then:

```bash
cd <path-to>/desktop-provision
python scripts/discover_and_fill.py
python scripts/preflight.py
python scripts/provision.py    # skip if REUSE
python scripts/verify.py       # Flask + auto pip install vm_requirements.txt on VM
# when done:
python scripts/delete.py
```

### Instance type vs region

`ecs.g8a.xlarge` is not sold in every zone. Discover picks a vSwitch zone where your type is available; if the preferred region lacks it, other regions with the same image are tried. Discover never changes `ALIYUN_INSTANCE_TYPE`.

### Cold start

After `provision.py`, SSH and Flask may need **1–3 minutes** to start. This is normal — `verify.py` retries automatically. See [SKILL.md § Cold start](SKILL.md#cold-start-important).

After verify passes, `verify.py` also runs `pip3 install -r <repo>/vm_requirements.txt` on the VM (or skips if already installed). First run may take several minutes.

### Billing

PostPaid ECS requires account balance. Recharge before `provision.py`.
