import sys
import pytest

sys.path.append('rplugin/python3/')

from vimtitles import Timestamp, TimestampPair

class TestTimestamp:

    invalid_ts = [
        '00:00:000,000',
        '00:000:00,000',
        '00:00:00,0000',
        '000:00:00,000',
        '00:00:00.000',
        '00:00:61,000',
        '00:61:00,000',
        '00:00:00,000 --> 00:00:00,000',
    ]

    valid_ts = [
        ('00:00:00,000', 0),
        ('01:02:03,000', 3723.0),
        ('00:03:05,750', 185.750),
    ]

    shift_ts = [
        ('00:00:00,000', -5, '00:00:00,000'),
        ('00:00:00,000', 5, '00:00:05,000'),
        ('00:00:00,000', 5.750, '00:00:05,750'),
        ('00:00:10,000', -5, '00:00:05,000'),
        ('00:00:00,000', 60, '00:01:00,000'),
    ]

    @pytest.mark.parametrize("ts", invalid_ts)
    def test_format_error(self, ts):
        with pytest.raises(Exception):
            Timestamp.from_string(ts)

    @pytest.mark.parametrize("ts,secs", valid_ts)
    def test_from_string(self, ts, secs):
        t = Timestamp.from_string(ts)
        assert t.seconds == float(secs)

    @pytest.mark.parametrize("ts,secs", valid_ts)
    def test_to_string(self, ts, secs):
        t = Timestamp(secs)
        assert str(t) == ts

    def test_no_negatives(self):
        with pytest.raises(Exception, match=r'.* greater than zero'):
            Timestamp(-1)

    @pytest.mark.parametrize("ts,secs,ts_out", shift_ts)
    def test_shift(self, ts, secs, ts_out):
        t = Timestamp.from_string(ts)
        t.shift(secs)
        assert str(t) == ts_out


class TestTimestampPair:

    invalid_ts_pairs = [
        '00:00:000,000 --> 00:00:00,000',
        '00:00:00,000 --> 00:00:000,000',
        '00:00:00,000 -> 00:00:00,000',
        '00:00:00,000 --> 00:00:00,000 hello',
        '00:00:00,000 --> 00:00:79,000',
    ]

    valid_ts_pairs = [
        ('00:00:00,000 --> 00:00:05,000', -5, '00:00:00,000 --> 00:00:00,000'),
        ('00:00:10,333 --> 00:01:15,000', 5, '00:00:15,333 --> 00:01:20,000'),
        ('00:01:00,000 --> 00:03:05,000', 60, '00:02:00,000 --> 00:04:05,000'),
        ('00:00:50,000 --> 00:00:55,000', 5.125, '00:00:55,125 --> 00:01:00,125'),
    ]

    @pytest.mark.parametrize("ts", invalid_ts_pairs)
    def test_format_error(self, ts):
        with pytest.raises(Exception, match=r'not a valid srt timestamp'):
            TimestampPair(ts)

    def test_timestamp_order(self):
        with pytest.raises(Exception, match=r'First timestamp must .*'):
            TimestampPair('00:00:15,000 --> 00:00:10,000',)

    @pytest.mark.parametrize("ts,secs,ts_out", valid_ts_pairs)
    def test_init(self, ts, secs, ts_out):
        t = TimestampPair(ts)
        assert str(t) == ts

    @pytest.mark.parametrize("ts,secs,ts_out", valid_ts_pairs)
    def test_shift(self, ts, secs, ts_out):
        t = TimestampPair(ts)
        t.shift(secs)
        assert str(t) == ts_out

