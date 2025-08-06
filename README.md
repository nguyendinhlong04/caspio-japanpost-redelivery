# caspio-japanpost-redelivery

Tự động lấy danh sách đơn **“Vắng nhà”** trên Caspio và đặt lại lịch giao qua Japan Post.

## Cài cục bộ

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export CASPIO_CLIENT_ID=...
export CASPIO_CLIENT_SECRET=...

python -m jp_redelivery.cli
