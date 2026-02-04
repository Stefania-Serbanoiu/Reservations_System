import json
import sys
from urllib import request, parse, error

BASE = "http://127.0.0.1:8000"


def http(method: str, path: str, body=None, qs=None):
    url = BASE + path
    if qs:
        url += "?" + parse.urlencode(qs)

    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"detail": raw}


def p(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def help():
    print(
        """
Commands:
  create-user <username> [--admin]
  list-users
  login <username>
  add-room <admin_user_id> <name> <capacity>
  list-rooms [--mincap N] [--maxcap N]
  reserve <user_id> <room_id> <start_date> <end_date>
  cancel <actor_user_id> <reservation_id>
  my-reservations <user_id> [--all]
  availability <start_date> <end_date> [--mincap N]
  occupancy <YYYY-MM-DD>

Type 0 to exit.

Examples:
    create-user alice
    create-user admin --admin
    add-room 2 "Sala A1" 20
    reserve 1 1 2026-01-21 2026-01-23
    list-users
    list-rooms --mincap 10
    reserve 1 1 2026-01-21 2026-01-23
    availability 2026-01-21 2026-01-21 --mincap 10
    my-reservations 1
    cancel 1 1
    occupancy 2026-01-21
"""
    )


def main_loop():
    help()

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if line == "0":
            print("Bye")
            break

        if not line:
            continue

        argv = ["cli.py"] + line.split()
        cmd = argv[1]

        try:
            if cmd == "create-user":
                username = argv[2]
                is_admin = "--admin" in argv
                status, out = http("POST", "/users", {"username": username, "is_admin": is_admin})
                print(status); p(out)

            elif cmd == "login":
                username = argv[2]
                status, out = http("GET", f"/users/by-username/{parse.quote(username)}")
                print(status); p(out)

            elif cmd == "add-room":
                admin_user_id = int(argv[2])
                name = argv[3]
                capacity = int(argv[4])
                status, out = http(
                    "POST", "/resources",
                    {"name": name, "type": "room", "capacity": capacity},
                    qs={"admin_user_id": admin_user_id}
                )
                print(status); p(out)

            elif cmd == "list-rooms":
                qs = {"type": "room"}
                if "--mincap" in argv:
                    qs["min_capacity"] = int(argv[argv.index("--mincap") + 1]) 
                if "--maxcap" in argv:
                    qs["max_capacity"] = int(argv[argv.index("--maxcap") + 1]) 
                status, out = http("GET", "/resources", qs=qs)
                print(status); p(out)

            elif cmd == "reserve":
                user_id = int(argv[2]); room_id = int(argv[3])
                start_date = argv[4]; end_date = argv[5]
                status, out = http("POST", "/reservations", {
                    "user_id": user_id,
                    "resource_id": room_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                print(status); p(out)

            elif cmd == "cancel":
                actor_user_id = int(argv[2])
                reservation_id = int(argv[3])
                status, out = http(
                    "POST",
                    f"/reservations/{reservation_id}/cancel",
                    qs={"actor_user_id": actor_user_id}
                )
                print(status); p(out)

            elif cmd == "my-reservations":
                user_id = int(argv[2])
                include_cancelled = "--all" in argv
                status, out = http(
                    "GET",
                    f"/users/{user_id}/reservations",
                    qs={"include_cancelled": include_cancelled}
                )
                print(status); p(out)

            elif cmd == "availability":
                start_date = argv[2]; end_date = argv[3]
                qs = {"start_date": start_date, "end_date": end_date}
                if "--mincap" in argv:
                    qs["min_capacity"] = int(argv[argv.index("--mincap") + 1]) 
                status, out = http("GET", "/availability", qs=qs)
                print(status); p(out)

            elif cmd == "occupancy":
                day = argv[2]
                status, out = http("GET", "/reports/occupancy", qs={"day": day})
                print(status); p(out)

            elif cmd == "list-users":
                status, out = http("GET", "/users/")
                print(status); p(out)

            else:
                help()

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main_loop()
