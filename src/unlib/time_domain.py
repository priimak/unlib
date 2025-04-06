import re
from enum import IntEnum, Enum
from typing import Self, Any


class FrequencyUnit(Enum):
    GHz = "GHz"
    MHz = "MHz"
    KHz = "KHz"
    Hz = "Hz"

    def period_in_seconds(self) -> float:
        match self:
            case FrequencyUnit.Hz:
                return 1
            case FrequencyUnit.KHz:
                return 0.001
            case FrequencyUnit.MHz:
                return 1e-6
            case FrequencyUnit.GHz:
                return 1e-9
            case _:
                raise RuntimeError("Invalid frequency unit")

    @staticmethod
    def value_of(src: Any) -> "FrequencyUnit":
        if isinstance(src, FrequencyUnit):
            return src
        elif isinstance(src, str):
            match src.strip().lower():
                case "thz":
                    return FrequencyUnit.THz
                case "ghz":
                    return FrequencyUnit.GHz
                case "mhz":
                    return FrequencyUnit.MHz
                case "khz":
                    return FrequencyUnit.KHz
                case "hz":
                    return FrequencyUnit.Hz
                case _:
                    raise ValueError(f"Unknown frequency unit: {src}")
        else:
            raise ValueError(f"Unknown frequency unit: {src}")

    def matching_time_unit(self) -> "TimeUnit":
        match self:
            case FrequencyUnit.Hz:
                return TimeUnit.S
            case FrequencyUnit.KHz:
                return TimeUnit.MS
            case FrequencyUnit.MHz:
                return TimeUnit.US
            case FrequencyUnit.GHz:
                return TimeUnit.NS


class TimeUnit(IntEnum):
    NS = 1
    US = 1_000
    MS = 1_000_000
    S = 1_000_000_000
    KS = 1_000_000_000_000

    @staticmethod
    def value_of(s: Any) -> "TimeUnit":
        if isinstance(s, TimeUnit):
            return s
        else:
            match f"{s}".lower():
                case "ns":
                    return TimeUnit.NS
                case "us":
                    return TimeUnit.US
                case "ms":
                    return TimeUnit.MS
                case "s":
                    return TimeUnit.S
                case "ks":
                    return TimeUnit.KS
                case _:
                    raise RuntimeError(f"Unknown time unit: {s}")

    def to_str(self) -> str:
        match self:
            case TimeUnit.NS:
                return "ns"
            case TimeUnit.US:
                return "us"
            case TimeUnit.MS:
                return "ms"
            case TimeUnit.S:
                return "s"
            case TimeUnit.KS:
                return "ks"
            case _:
                raise RuntimeError(f"Unknown time unit: {self}")


class Duration:
    __matcher = re.compile(
        r"""^\s*(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?P<unit>ks|s|ms|us|ns|KS|S|MS|US|NS)\s*$"""
    )

    def __init__(self, time_interval: float, time_unit: TimeUnit):
        self.value = time_interval
        self.time_unit = time_unit

    def __str__(self):
        return f"{self.value} {self.time_unit.to_str()}"

    def __repr__(self):
        return f"Duration({self.value}, {self.time_unit.to_str()})"

    def __add__(self, other):
        if isinstance(other, Duration):
            return Duration(
                time_interval=self.value + other.to_float(self.time_unit),
                time_unit=self.time_unit
            ).optimize()

    def __sub__(self, other):
        if isinstance(other, Duration):
            return Duration(
                time_interval=self.value - other.to_float(self.time_unit),
                time_unit=self.time_unit
            ).optimize()

    def __mul__(self, scale):
        return Duration(self.value * scale, self.time_unit)

    def __rmul__(self, scale):
        return Duration(self.value * scale, self.time_unit)

    def __truediv__(self, scale):
        return Duration(self.value / scale, self.time_unit)

    def __gt__(self, other):
        if isinstance(other, Duration):
            return self.value > other.to_float(self.time_unit)
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __ge__(self, other):
        if isinstance(other, Duration):
            return self.value > other.to_float(self.time_unit) or self == other
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __lt__(self, other):
        if isinstance(other, Duration):
            return self.value < other.to_float(self.time_unit)
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __le__(self, other):
        if isinstance(other, Duration):
            return self.value < other.to_float(self.time_unit) or self == other
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __eq__(self, other):
        if isinstance(other, Duration):
            return abs(self - other) < ONE_PICOSECOND
        else:
            raise RuntimeError("Duration can only be compared to another duration")

    def __abs__(self):
        return Duration(abs(self.value), self.time_unit)

    def in_unit(self, time_unit: str | TimeUnit) -> Self:
        target_time_unit = TimeUnit.value_of(time_unit)
        return Duration(
            self.value * self.time_unit.value / target_time_unit.value,
            target_time_unit
        )

    @staticmethod
    def value_of(s: Any) -> "Duration":
        if isinstance(s, Duration):
            return s
        match_result = Duration.__matcher.match(f"{s}")
        if match_result:
            return Duration(float(match_result.group('value')), TimeUnit.value_of(match_result.group('unit')))
        else:
            raise RuntimeError(f"Unable to parse \"{s}\" as duration")

    def to_float(self, time_unit: str | TimeUnit) -> float:
        return self.value * self.time_unit.value / TimeUnit.value_of(time_unit).value

    def optimize(self) -> Self:
        for time_unit in [TimeUnit.KS, TimeUnit.S, TimeUnit.MS, TimeUnit.US, TimeUnit.NS]:
            if 1000 > self.to_float(time_unit) >= 1:
                return self.in_unit(time_unit)

        return self.in_unit(TimeUnit.NS)


class Frequency:
    def __init__(self, freq: float, unit: FrequencyUnit):
        self.__freq = freq
        self.__unit = unit

    @staticmethod
    def value_of(src: Any) -> "Frequency":
        if isinstance(src, Frequency):
            return src
        elif isinstance(src, str):
            src_clean = src.strip().lower()
            if src_clean.endswith("ghz"):
                return Frequency(float(src_clean.replace("ghz", "")), FrequencyUnit.GHz)
            elif src_clean.endswith("mhz"):
                return Frequency(float(src_clean.replace("mhz", "")), FrequencyUnit.MHz)
            elif src_clean.endswith("khz"):
                return Frequency(float(src_clean.replace("khz", "")), FrequencyUnit.KHz)
            elif src_clean.endswith("hz"):
                return Frequency(float(src_clean.replace("hz", "")), FrequencyUnit.Hz)
            else:
                raise RuntimeError(f"Unable to parse [{src}]")
        else:
            raise ValueError(f"Unable to parse [{src}]")

    def __add__(self, other) -> "Frequency":
        if isinstance(other, Frequency):
            return Frequency(self.__freq + other.as_float(self.__unit), self.__unit)
        else:
            raise ValueError(f"Frequency can only be added to another Frequency")

    def __sub__(self, other) -> "Frequency":
        if isinstance(other, Frequency):
            return Frequency(self.__freq - other.as_float(self.__unit), self.__unit)
        else:
            raise ValueError(f"Frequency can only be subtracted from another Frequency")

    def __rtruediv__(self, other) -> "Duration":
        if isinstance(other, int) or isinstance(other, float):
            return Duration(1 / self.as_float(), self.__unit.matching_time_unit())
        else:
            raise ValueError(f"Frequency can only divide a number")

    def __truediv__(self, other) -> "Frequency":
        if isinstance(other, int) or isinstance(other, float):
            return Frequency(self.__freq / other, self.__unit)
        else:
            raise ValueError("Frequency can only be divided by a number")

    def __rmul__(self, other) -> "Frequency":
        if isinstance(other, int) or isinstance(other, float):
            return Frequency(other * self.__freq, self.__unit)
        else:
            raise ValueError("Frequency can only be multiplied by a number")

    def __mul__(self, other) -> "Frequency":
        if isinstance(other, int) or isinstance(other, float):
            return Frequency(self.__freq * other, self.__unit)
        else:
            raise ValueError(f"Frequency can only be multiplied by a number")

    def __lt__(self, other) -> bool:
        if not isinstance(other, Frequency):
            raise TypeError(f"Cannot compare {self} to {other}")
        else:
            return self.__freq < other.as_float(self.__unit)

    def __le__(self, other) -> bool:
        return self == other or self < other

    def __eq__(self, other) -> bool:
        if not isinstance(other, Frequency):
            return False
        elif self.__unit == other.__unit:
            return self.__freq == other.__freq
        else:
            return self.__freq == other.as_float(self.__unit)

    def __repr__(self):
        return f"{self.__freq} {self.__unit.value}"

    def as_float(self, unit: FrequencyUnit | str | None = None) -> float:
        if unit is None:
            return self.__freq
        else:
            return self.__freq * FrequencyUnit.value_of(unit).period_in_seconds() / self.__unit.period_in_seconds()

    def in_unit(self, unit: str | FrequencyUnit) -> "Frequency":
        return Frequency(self.as_float(unit), FrequencyUnit.value_of(unit))

    @property
    def unit(self) -> FrequencyUnit:
        return self.__unit


ONE_PICOSECOND = Duration.value_of("0.001ns")
