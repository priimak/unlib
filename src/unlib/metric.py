import re
from enum import Enum
from typing import Self, Any


class Scale(Enum):
    NANO = 1e-9
    MICRO = 1e-6
    MILLI = 1e-3
    UNIT = 1.0
    KILO = 1e3
    MEGA = 1e6
    GIGA = 1e9

    def to_str(self):
        match self:
            case Scale.NANO:
                return "n"
            case Scale.MICRO:
                return "u"
            case Scale.MILLI:
                return "m"
            case Scale.UNIT:
                return ""
            case Scale.KILO:
                return "K"
            case Scale.MEGA:
                return "M"
            case Scale.GIGA:
                return "G"

    @staticmethod
    def value_of(s: Any) -> "Scale":
        if isinstance(s, Scale):
            return s
        else:
            in_str = f"{s}".strip()
            if len(in_str) == 0:
                return Scale.UNIT

            match in_str[0]:
                case "n":
                    return Scale.NANO
                case "u":
                    return Scale.MICRO
                case "m":
                    return Scale.MILLI
                case "":
                    return Scale.UNIT
                case "K":
                    return Scale.KILO
                case "M":
                    return Scale.MEGA
                case "G":
                    return Scale.GIGA
                case _:
                    raise RuntimeError(f"Unknown scale in \"{s}\"")


class MetricValue:
    __matcher = re.compile(
        r"""^\s*(?P<value>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(?P<scale>n|u|m|K|M|G|)(?P<phys_unit>\S+)\s*$"""
    )

    def __init__(self, value: float, scale: Scale, phys_unit: str):
        self.value = value
        self.scale = scale
        self.phys_unit = phys_unit

    def __hash__(self):
        return hash(self.value) + hash(self.scale) + hash(self.phys_unit)

    def __str__(self):
        return f"{self.value} {self.scale.to_str()}{self.phys_unit}"

    def __repr__(self):
        return f"MetricValue({self.value}, {self.scale.to_str()}{self.phys_unit})"

    @staticmethod
    def value_of(s: Any) -> "MetricValue":
        if isinstance(s, MetricValue):
            return s

        match_result = MetricValue.__matcher.match(f"{s}")
        if match_result:
            return MetricValue(
                value=float(match_result.group("value")),
                scale=Scale.value_of(match_result.group("scale")),
                phys_unit=match_result.group("phys_unit")
            )
        else:
            raise RuntimeError(f"Unable to parse \"{s}\" as duration")

    def to_float(self, scale: str | Scale) -> float:
        return self.value * self.scale.value / Scale.value_of(scale).value

    def in_unit(self, scale: str | Scale) -> Self:
        target_scale = Scale.value_of(scale)
        return MetricValue(
            self.value * self.scale.value / target_scale.value,
            target_scale,
            self.phys_unit
        )

    def optimize(self) -> Self:
        for scale in Scale:
            if 1000 > abs(self.to_float(scale)) >= 1:
                return self.in_unit(scale)

        return self.in_unit(Scale.NANO)

    def __add__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be added only if they share the same physical unit")
            return MetricValue(
                value=self.value + other.to_float(self.scale),
                scale=self.scale,
                phys_unit=self.phys_unit
            ).optimize()
        else:
            raise RuntimeError("Metric values can only be added to other metric values")

    def __sub__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be subtracted only if they share the same physical unit")
            return MetricValue(
                value=self.value - other.to_float(self.scale),
                scale=self.scale,
                phys_unit=self.phys_unit
            ).optimize()

    def __mul__(self, scale):
        return MetricValue(self.value * scale, self.scale, self.phys_unit).optimize()

    def __rmul__(self, scale):
        return MetricValue(self.value * scale, self.scale, self.phys_unit).optimize()

    def __truediv__(self, scale):
        return MetricValue(self.value / scale, self.scale, self.phys_unit).optimize()

    def __gt__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be compared only if they share the same physical unit")
            return self.value > other.to_float(self.scale)
        else:
            raise RuntimeError("MetricValue can only be compared to another metric value")

    def __ge__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be compared only if they share the same physical unit")
            return self.value > other.to_float(self.scale) or self == other
        else:
            raise RuntimeError("MetricValue can only be compared to another metric value")

    def __lt__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be compared only if they share the same physical unit")
            return self.value < other.to_float(self.scale)
        else:
            raise RuntimeError("MetricValue can only be compared to another metric value")

    def __le__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be compared only if they share the same physical unit")
            return self.value < other.to_float(self.scale) or self == other
        else:
            raise RuntimeError("MetricValue can only be compared to another metric value")

    def __eq__(self, other):
        if isinstance(other, MetricValue):
            if self.phys_unit != other.phys_unit:
                raise RuntimeError("Values can be compared only if they share the same physical unit")
            return abs(self - other).to_float(Scale.NANO) < 0.001
        else:
            raise RuntimeError("MetricValue can only be compared to another metric value")

    def __abs__(self):
        return MetricValue(abs(self.value), self.scale, self.phys_unit)
