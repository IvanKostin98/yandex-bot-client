"""Сборка inline-клавиатур и helper для мультивыбора."""

from typing import Any, Dict, List, Optional, Sequence, Set


class Keyboard:
    """Ряды кнопок через .row(...). В конце — .build() и передать в send_message(..., keyboard=...)."""

    def __init__(self) -> None:
        self._rows: List[List[Dict[str, Any]]] = []

    @staticmethod
    def button(
        text: str,
        cmd: Optional[str] = None,
        *,
        callback_data: Optional[Dict[str, Any]] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Одна кнопка. cmd — команда при нажатии (в button_handler попадёт без слэша). callback_data — свой dict; если есть cmd, он туда добавится. Только свои поля без cmd — обрабатывай в callback_handler. url — кнопка-ссылка."""
        data = callback_data.copy() if callback_data else {}
        if cmd:
            data["cmd"] = cmd if cmd.startswith("/") else f"/{cmd}"
        btn: Dict[str, Any] = {"text": text, "callback_data": data}
        if url:
            btn["url"] = url
        return btn

    def row(self, *buttons: Dict[str, Any]) -> "Keyboard":
        """Добавляет ряд кнопок. Можно несколько кнопок в один ряд. Возвращает self для цепочки."""
        self._rows.append(list(buttons))
        return self

    def build(self) -> List[List[Dict[str, Any]]]:
        """Готовый формат для send_message(..., keyboard=...)."""
        return self._rows

    @staticmethod
    def from_rows(rows: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """Собрать из готовых рядов (список списков кнопок)."""
        return rows


class MultiSelectKeyboard:
    """Helper для мультивыбора через inline-кнопки с чекбоксами."""

    def __init__(
        self,
        items: Sequence[Dict[str, str]],
        selected: Optional[Sequence[str]] = None,
        *,
        id_key: str = "id",
        text_key: str = "text",
        toggle_cmd: str = "/ms_toggle",
        all_cmd: str = "/ms_all",
        done_cmd: str = "/ms_done",
        cancel_cmd: Optional[str] = "/ms_cancel",
        selected_icon: str = "✅",
        unselected_icon: str = "◻️",
        all_text: str = "✅ Выбрать всё",
        clear_text: str = "❌ Снять всё",
        done_text: str = "➡️ Продолжить",
        cancel_text: Optional[str] = "🔙 Назад",
    ) -> None:
        self._items: List[Dict[str, str]] = [dict(i) for i in items]
        self._selected: Set[str] = set(selected or [])
        self._id_key = id_key
        self._text_key = text_key
        self._toggle_cmd = toggle_cmd
        self._all_cmd = all_cmd
        self._done_cmd = done_cmd
        self._cancel_cmd = cancel_cmd
        self._selected_icon = selected_icon
        self._unselected_icon = unselected_icon
        self._all_text = all_text
        self._clear_text = clear_text
        self._done_text = done_text
        self._cancel_text = cancel_text

    def selected(self) -> List[str]:
        """Текущий список выбранных id."""
        return list(self._selected)

    def set_selected(self, selected: Sequence[str]) -> "MultiSelectKeyboard":
        """Полностью заменить выбранные id."""
        self._selected = set(selected)
        return self

    def toggle(self, item_id: str) -> "MultiSelectKeyboard":
        """Переключить состояние одного элемента."""
        if item_id in self._selected:
            self._selected.remove(item_id)
        else:
            self._selected.add(item_id)
        return self

    def select_all(self) -> "MultiSelectKeyboard":
        """Выбрать все элементы."""
        self._selected = {str(item.get(self._id_key, "")) for item in self._items if item.get(self._id_key)}
        return self

    def clear_all(self) -> "MultiSelectKeyboard":
        """Снять выделение со всех элементов."""
        self._selected.clear()
        return self

    def build(self) -> List[List[Dict[str, Any]]]:
        """Собрать inline-клавиатуру для мультивыбора."""
        kb = Keyboard()
        item_ids = [str(item.get(self._id_key, "")) for item in self._items]

        for item in self._items:
            item_id = str(item.get(self._id_key, ""))
            item_text = str(item.get(self._text_key, item_id))
            icon = self._selected_icon if item_id in self._selected else self._unselected_icon
            kb.row(
                Keyboard.button(
                    f"{icon} {item_text}",
                    callback_data={"cmd": self._toggle_cmd, "id": item_id},
                )
            )

        has_items = bool(item_ids)
        all_selected = has_items and all(item_id in self._selected for item_id in item_ids)
        kb.row(
            Keyboard.button(
                self._clear_text if all_selected else self._all_text,
                callback_data={"cmd": self._all_cmd},
            )
        )
        kb.row(Keyboard.button(self._done_text, callback_data={"cmd": self._done_cmd}))
        if self._cancel_text and self._cancel_cmd:
            kb.row(Keyboard.button(self._cancel_text, callback_data={"cmd": self._cancel_cmd}))
        return kb.build()
