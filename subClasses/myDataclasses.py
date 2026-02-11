from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, ClassVar


@dataclass
class command_array:
    # Class-level registry of all created AppEntry instances
    all_commands_dict: ClassVar[Dict[str, "command_array"]] = {}
    name: str
    ids_array: List[int]
    hotkey_array: List[str] 

    def __post_init__(self) -> None:
        cls = type(self)
        if not hasattr(cls, "all_commands_dict"):
            cls.all_commands_dict = {}
            print("created command_array class-level all_commands_dict dict")
        if self.name not in cls.all_commands_dict:
            cls.all_commands_dict[self.name] = self


    


