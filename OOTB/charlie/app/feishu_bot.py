"""飞书群聊机器人 — WebSocket 长连接接收事件，无需公网 URL

使用 lark-oapi SDK 的 WebSocket 模式:
  飞书群消息 → 长连接推送 → handle_message()
  → sender_id 生成 session_id → brain(text, session_id)
  → 回复到群聊

配置:
  FEISHU_BOT_ENABLED=1           启用群聊机器人
  FEISHU_BOT_AT_ONLY=1           群聊中仅 @Charlie 时回复
"""
import os
import json
import re
import logging
import threading

log = logging.getLogger("magic")

FEISHU_BASE = "https://open.feishu.cn/open-apis"
BOT_ENABLED = os.getenv("FEISHU_BOT_ENABLED", "0") == "1"
AT_ONLY = os.getenv("FEISHU_BOT_AT_ONLY", "1") == "1"

# @ 消息前缀: @_user_1 等
_AT_MENTION_RE = re.compile(r"@_user_\d+\s*|@\S+\s*")

# 事件去重
_seen_events: set[str] = set()
_seen_lock = threading.Lock()
_SEEN_MAX = 500  # 最多保留500个事件ID

# 全局 WS client
_ws_client = None
_ws_thread = None


def _get_token() -> str:
    """获取 tenant_access_token"""
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        return ""
    try:
        import requests
        r = requests.post(f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        return r.json().get("tenant_access_token", "")
    except Exception:
        return ""


def _reply_to_chat(chat_id: str, text: str) -> bool:
    """回复消息到飞书群聊/单聊"""
    token = _get_token()
    if not token:
        return False
    try:
        import requests
        r = requests.post(
            f"{FEISHU_BASE}/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False),
            },
            timeout=10,
        )
        if r.status_code == 200 and r.json().get("code") == 0:
            log.info(f"[feishu-bot] 回复成功: {text[:40]}")
            return True
        log.warning(f"[feishu-bot] 回复失败: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        log.warning(f"[feishu-bot] 回复异常: {e}")
        return False


def _process_message(text: str, sender_id: str, chat_id: str):
    """处理消息: 调用 brain 并回复（在独立线程中执行）"""
    session_id = f"feishu-{sender_id}" if sender_id else "feishu-group"
    try:
        from voice_agent import brain
        reply = brain(text, session_id=session_id)
        if reply:
            _reply_to_chat(chat_id, reply)
    except Exception as e:
        log.error(f"[feishu-bot] 处理失败: {e}")
        try:
            _reply_to_chat(chat_id, "处理消息时出错了，请稍后再试。")
        except Exception:
            pass


def _register_event_handler():
    """注册飞书消息事件处理器，返回 dispatcher"""
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

    def handle_message(ctx, conf, event: P2ImMessageReceiveV1) -> None:
        try:
            # 事件去重
            event_id = event.header.event_id if event.header else ""
            if event_id:
                with _seen_lock:
                    if event_id in _seen_events:
                        return
                    _seen_events.add(event_id)
                    if len(_seen_events) > _SEEN_MAX:
                        _seen_events.clear()

            msg = event.event.message if event.event else None
            sender = event.event.sender if event.event else None
            if not msg:
                return

            # 只处理文本消息
            if msg.message_type != "text":
                return

            chat_type = msg.chat_type  # "group" or "p2p"
            chat_id = msg.chat_id
            sender_id = ""
            if sender and sender.sender_id:
                sender_id = sender.sender_id.open_id or ""

            # 解析文本
            try:
                content = json.loads(msg.content or "{}")
                text = content.get("text", "")
            except Exception:
                text = ""

            # 去除 @ 前缀
            text = _AT_MENTION_RE.sub("", text).strip()
            if not text:
                return

            # 群聊中检查是否 @ 了机器人
            if chat_type == "group" and AT_ONLY:
                mentions = msg.mentions or []
                at_bot = any(
                    m.id and m.id.open_id and m.name and ("Charlie" in m.name or "charlie" in m.name.lower())
                    for m in mentions
                ) if mentions else False
                # 也检查 @_user_1 模式（飞书将@机器人转为@_user_1）
                if not at_bot:
                    try:
                        raw_content = json.loads(msg.content or "{}")
                        if "@_user_1" in raw_content.get("text", ""):
                            at_bot = True
                    except Exception:
                        pass
                if not at_bot:
                    return

            log.info(f"[feishu-bot] 收到消息 [{chat_type}] {text[:50]}")
            threading.Thread(
                target=_process_message,
                args=(text, sender_id, chat_id),
                daemon=True,
            ).start()

        except Exception as e:
            log.error(f"[feishu-bot] 事件处理异常: {e}", exc_info=True)

    # 创建事件分发器并注册 handler
    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message) \
        .build()
    return event_handler


def start_feishu_bot():
    """启动飞书 WebSocket 长连接客户端（在独立线程中）"""
    global _ws_client, _ws_thread

    if not BOT_ENABLED:
        log.info("[feishu-bot] 未启用（FEISHU_BOT_ENABLED=0）")
        return False

    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        log.warning("[feishu-bot] FEISHU_APP_ID/SECRET 未配置，跳过启动")
        return False

    if _ws_client is not None:
        log.info("[feishu-bot] 已在运行")
        return True

    try:
        import lark_oapi as lark

        event_handler = _register_event_handler()
        _ws_client = lark.ws.Client(
            app_id,
            app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.WARNING,
            auto_reconnect=True,
        )

        def _run():
            try:
                log.info("[feishu-bot] WebSocket 长连接启动中...")
                _ws_client.start()
            except Exception as e:
                log.error(f"[feishu-bot] WebSocket 连接异常: {e}")

        _ws_thread = threading.Thread(target=_run, daemon=True, name="feishu-ws")
        _ws_thread.start()
        log.info("[feishu-bot] WebSocket 长连接已启动（无需公网URL）")
        return True

    except Exception as e:
        log.error(f"[feishu-bot] 启动失败: {e}")
        _ws_client = None
        return False


def stop_feishu_bot():
    """停止飞书 WebSocket 客户端"""
    global _ws_client, _ws_thread
    if _ws_client:
        try:
            # lark ws Client 没有显式 stop，断开靠进程退出
            _ws_client = None
            _ws_thread = None
            log.info("[feishu-bot] 已停止")
        except Exception:
            pass


def get_bot_status() -> dict:
    """返回机器人状态"""
    return {
        "enabled": BOT_ENABLED,
        "at_only": AT_ONLY,
        "configured": bool(os.getenv("FEISHU_APP_ID") and os.getenv("FEISHU_APP_SECRET")),
        "running": _ws_client is not None,
        "mode": "websocket",
    }
