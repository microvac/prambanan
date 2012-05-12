var JS, __builtin__, __import__, __log10__, __log2__, __py_file__, _isUndefined, _iter, _m___pyjamas__, _pow, _subscript, _throw, abs, acos, asin, atan, atan2, ceil, cos, degrees, e, enumerate, exp, fabs, float, floor, frexp, fsum, hypot, int, ldexp, log, log10, max, min, pi, pow, radians, sin, sqrt, tan;
__builtin__ = prambanan.import('__builtin__');
min = __builtin__.min;
int = __builtin__.int;
__import__ = __builtin__.__import__;
float = __builtin__.float;
enumerate = __builtin__.enumerate;
abs = __builtin__.abs;
max = __builtin__.max;
_iter = prambanan.helpers.iter;
_pow = prambanan.helpers.pow;
_subscript = prambanan.helpers.subscript;
__py_file__ = 'math.py';
_isUndefined = prambanan.helpers._.isUndefined;
_throw = prambanan.helpers.
throw;
(function(prambanan) {
    _m___pyjamas__ = __import__('__pyjamas__');
    JS = _m___pyjamas__.JS;
    ceil = function(x) {
        return float(Math.ceil(x.valueOf()));
    };
    fabs = function(x) {
        return float(Math.abs(x.valueOf()));
    };
    floor = function(x) {
        return float(Math.floor(x.valueOf()));
    };
    exp = function(x) {
        return float(Math.exp(x.valueOf()));
    };
    log = function(x, base) {
        if (_isUndefined(base)) base = null;
        if (base === null) {
            return float(Math.log(x.valueOf()));
        }
        return float(Math.log(x.valueOf()) / Math.log(base.valueOf()));
    };
    pow = function(x, y) {
        return float(Math.pow(x.valueOf(), y.valueOf()));
    };
    sqrt = function(x) {
        return float(Math.sqrt(x.valueOf()));
    };
    cos = function(x) {
        return float(Math.cos(x.valueOf()));
    };
    sin = function(x) {
        return float(Math.sin(x.valueOf()));
    };
    tan = function(x) {
        return float(Math.tan(x.valueOf()));
    };
    acos = function(x) {
        return float(Math.acos(x.valueOf()));
    };
    asin = function(x) {
        return float(Math.asin(x.valueOf()));
    };
    atan = function(x) {
        return float(Math.atan(x.valueOf()));
    };
    atan2 = function(x, y) {
        return float(Math.atan2(x.valueOf(), y.valueOf()));
    };
    pi = float(Math.PI);
    e = float(Math.E);
    __log10__ = float(Math.LN10);
    __log2__ = log(2);
    fsum = function(x) {
        var _i, _len, _list, i, sum, xx;
        xx = (function() {
            var _i, _len, _list, _results;
            _results = [];
            _list = _iter(enumerate(x));
            for (_i = 0, _len = _list.length; _i < _len; _i++) {
                i = _list[_i][0];
                v = _list[_i][1];
                _results.push([fabs(v), i]);
            }
            return _results;
        })();
        xx.sort();
        sum = 0;
        _list = xx;
        for (_i = 0, _len = _list.length; _i < _len; _i++) {
            i = _list[_i];
            sum += _subscript('load', x, 'index', i[1]);
        }
        return sum;
    };
    frexp = function(x) {
        var e, m;
        if (x === 0) {
            return [0.0, 0];
        }
        e = int(log(abs(x)) / __log2__) + 1;
        m = x / (_pow(2.0, e));
        return [m, e];
    };
    ldexp = function(x, i) {
        return x * (_pow(2, i));
    };
    log10 = function(arg) {
        return log(arg) / __log10__;
    };
    degrees = function(x) {
        return x * 180 / pi;
    };
    radians = function(x) {
        return x * pi / 180;
    };
    /**
     * Calculate the hypotenuse the safe way, avoiding over- and underflows
     */
    hypot = function(x, y) {
        var x, y;
        x = abs(x);
        y = abs(y);
        (function(_source) {
            x = _source[0];
            y = _source[1];
        })([max(x, y), min(x, y)]);
        return x * sqrt(1 + y / x * (y / x));
    };
    prambanan.exports('math', {
        acos: acos,
        asin: asin,
        atan: atan,
        atan2: atan2,
        ceil: ceil,
        cos: cos,
        degrees: degrees,
        e: e,
        exp: exp,
        fabs: fabs,
        floor: floor,
        frexp: frexp,
        fsum: fsum,
        hypot: hypot,
        ldexp: ldexp,
        log: log,
        log10: log10,
        pi: pi,
        pow: pow,
        radians: radians,
        sin: sin,
        sqrt: sqrt,
        tan: tan
    });
})(prambanan);
var JS, NotImplementedError, TypeError, ValueError, __builtin__, __c__days, __c__months, __import__, __py_file__, _dst, _isUndefined, _m___pyjamas__, _strptime, _subscript, _throw, altzone, asctime, ctime, d, float, gmtime, int, isinstance, len, localtime, math, mktime, object, str, strftime, strptime, struct_time, t_time_struct_time, time, timezone, tzname;
__builtin__ = prambanan.import('__builtin__');
object = __builtin__.object;
int = __builtin__.int;
__import__ = __builtin__.__import__;
float = __builtin__.float;
len = __builtin__.len;
TypeError = __builtin__.TypeError;
str = __builtin__.str;
NotImplementedError = __builtin__.NotImplementedError;
isinstance = __builtin__.isinstance;
ValueError = __builtin__.ValueError;
_throw = prambanan.helpers.
throw;
_subscript = prambanan.helpers.subscript;
__py_file__ = 'time.py';
_isUndefined = prambanan.helpers._.isUndefined;
(function(prambanan) {
    _m___pyjamas__ = __import__('__pyjamas__');
    JS = _m___pyjamas__.JS;
    math = __import__('math');
    timezone = 60 * (new Date(new Date().getFullYear(), 0, 1)).getTimezoneOffset();
    altzone = 60 * (new Date(new Date().getFullYear(), 6, 1)).getTimezoneOffset();
    if (altzone > timezone) {
        d = timezone;
        timezone = altzone;
        altzone = d;
    }
    _dst = timezone - altzone;
    d = (new Date(new Date().getFullYear(), 0, 1));
    d = _subscript('load', str(d.toLocaleString()).split(), 'index', -1);
    if (d[0] === "(") {
        d = _subscript('load', d, 'slice', 1, -1, null);
    }
    tzname = [d, null];
    delete d;
    __c__days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    __c__months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    time = function() {
        return float(new Date().getTime() / 1000.0);
    };

    function t_time_struct_time() {
        this.__init__.apply(this, arguments);
    }
    struct_time = object.extend({
        constructor: t_time_struct_time,
        n_fields: 9,
        n_sequence_fields: 9,
        n_unnamed_fields: 0,
        tm_year: null,
        tm_mon: null,
        tm_mday: null,
        tm_hour: null,
        tm_min: null,
        tm_sec: null,
        tm_wday: null,
        tm_yday: null,
        tm_isdst: null,
        __init__: function(ttuple) {
            if (_isUndefined(ttuple)) ttuple = null;
            if (!(ttuple === null)) {
                this.tm_year = ttuple[0];
                this.tm_mon = ttuple[1];
                this.tm_mday = ttuple[2];
                this.tm_hour = ttuple[3];
                this.tm_min = ttuple[4];
                this.tm_sec = ttuple[5];
                this.tm_wday = ttuple[6];
                this.tm_yday = ttuple[7];
                this.tm_isdst = ttuple[8];
            }
        },
        __str__: function() {
            var t;
            t = [this.tm_year, this.tm_mon, this.tm_mday, this.tm_hour, this.tm_min, this.tm_sec, this.tm_wday, this.tm_yday, this.tm_isdst];
            return t.__str__();
        },
        __repr__: function() {
            return this.__str__();
        },
        __getitem__: function(idx) {
            return _subscript('load', [this.tm_year, this.tm_mon, this.tm_mday, this.tm_hour, this.tm_min, this.tm_sec, this.tm_wday, this.tm_yday, this.tm_isdst], 'index', idx);
        },
        __getslice__: function(lower, upper) {
            return _subscript('load', [this.tm_year, this.tm_mon, this.tm_mday, this.tm_hour, this.tm_min, this.tm_sec, this.tm_wday, this.tm_yday, this.tm_isdst], 'slice', lower, upper, null);
        } /* static methods */
    });
    gmtime = function(t) {
        if (_isUndefined(t)) t = null;
        var date, startOfYear, t, tm, tm_year;
        if (t === null) {
            t = time();
        }
        date = new Date(t * 1000);
        tm = new struct_time();
        tm_year = tm.tm_year = int(date.getUTCFullYear());
        tm.tm_mon = int(date.getUTCMonth()) + 1;
        tm.tm_mday = int(date.getUTCDate());
        tm.tm_hour = int(date.getUTCHours());
        tm.tm_min = int(date.getUTCMinutes());
        tm.tm_sec = int(date.getUTCSeconds());
        tm.tm_wday = int(date.getUTCDay()) + 6 % 7;
        tm.tm_isdst = 0;
        startOfYear = new Date('Jan 1 ' + tm_year + ' GMT+0000');
        tm.tm_yday = 1 + int(t - startOfYear.getTime() / 1000 / 86400);
        return tm;
    };
    localtime = function(t) {
        if (_isUndefined(t)) t = null;
        var date, dateOffset, dt, startOfDay, startOfYear, startOfYearOffset, t, tm, tm_mday, tm_mon, tm_year;
        if (t === null) {
            t = time();
        }
        date = new Date(t * 1000);
        dateOffset = date.getTimezoneOffset();
        tm = new struct_time();
        tm_year = tm.tm_year = int(date.getFullYear());
        tm_mon = tm.tm_mon = int(date.getMonth()) + 1;
        tm_mday = tm.tm_mday = int(date.getDate());
        tm.tm_hour = int(date.getHours());
        tm.tm_min = int(date.getMinutes());
        tm.tm_sec = int(date.getSeconds());
        tm.tm_wday = int(date.getDay()) + 6 % 7;
        tm.tm_isdst = timezone === (60 * date.getTimezoneOffset()) ? 0 : 1;
        startOfYear = new Date(tm_year, 0, 1);
        startOfYearOffset = startOfYear.getTimezoneOffset();
        startOfDay = new Date(tm_year, tm_mon - 1, tm_mday);
        dt = float(startOfDay.getTime() - startOfYear.getTime()) / 1000;
        dt = dt + 60 * (startOfYearOffset - dateOffset);
        tm.tm_yday = 1 + int(dt / 86400.0);
        return tm;
    };
    /**
     * mktime(tuple) -> floating point number
     * Convert a time tuple in local time to seconds since the Epoch.
     */
    mktime = function(t) {
        var date, tm_hour, tm_mday, tm_min, tm_mon, tm_sec, tm_year, ts, utc;
        tm_year = t.tm_year;
        tm_mon = t.tm_mon - 1;
        tm_mday = t.tm_mday;
        tm_hour = t.tm_hour;
        tm_min = t.tm_min;
        tm_sec = t.tm_sec;
        date = new Date(tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec);
        utc = Date.UTC(tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec) / 1000;
        ts = date.getTime() / 1000;
        if (t[8] === 0) {
            if (ts - utc === timezone) {
                return ts;
            }
            return ts + _dst;
        }
        return ts;
    };
    strftime = function(fmt, t) {
        if (_isUndefined(t)) t = null;
        var date, firstMonday, firstWeek, format, re_pct, remainder, result, startOfYear, t, tm_hour, tm_mday, tm_min, tm_mon, tm_sec, tm_wday, tm_yday, tm_year, weekNo;
        if (t === null) {
            t = localtime();
        } else {
            if (!isinstance(t, struct_time) && len(t) !== 9) {
                _throw(new TypeError("argument must be 9-item sequence, not float"), __py_file__, 143);
            }
        }
        tm_year = t.tm_year;
        tm_mon = t.tm_mon;
        tm_mday = t.tm_mday;
        tm_hour = t.tm_hour;
        tm_min = t.tm_min;
        tm_sec = t.tm_sec;
        tm_wday = t.tm_wday;
        tm_yday = t.tm_yday;
        date = new Date(tm_year, tm_mon - 1, tm_mday, tm_hour, tm_min, tm_sec);
        startOfYear = new Date(tm_year, 0, 1);
        firstMonday = 1 - startOfYear.getDay() + 6 % 7 + 7;
        firstWeek = new Date(tm_year, 0, firstMonday);
        weekNo = date.getTime() - firstWeek.getTime();
        if (weekNo < 0) {
            weekNo = 0;
        } else {
            weekNo = 1 + int(weekNo / 604800000);
        }
        format = function(c) {
            if (c === "%") {
                return "%";
            } else {
                if (c === "a") {
                    return _subscript('load', format("A"), 'slice', null, 3, null);
                } else {
                    if (c === "A") {
                        return _subscript('load', __c__days, 'index', format("w"));
                    } else {
                        if (c === "b") {
                            return _subscript('load', format("B"), 'slice', null, 3, null);
                        } else {
                            if (c === "B") {
                                return _subscript('load', __c__months, 'index', tm_mon - 1);
                            } else {
                                if (c === "c") {
                                    return date.toLocaleString();
                                } else {
                                    if (c === "d") {
                                        return "%02d".sprintf(tm_mday);
                                    } else {
                                        if (c === "H") {
                                            return "%02d".sprintf(tm_hour);
                                        } else {
                                            if (c === "I") {
                                                return "%02d".sprintf(tm_hour % 12);
                                            } else {
                                                if (c === "j") {
                                                    return "%03d".sprintf(tm_yday);
                                                } else {
                                                    if (c === "m") {
                                                        return "%02d".sprintf(tm_mon);
                                                    } else {
                                                        if (c === "M") {
                                                            return "%02d".sprintf(tm_min);
                                                        } else {
                                                            if (c === "p") {
                                                                if (tm_hour < 12) {
                                                                    return "AM";
                                                                }
                                                                return "PM";
                                                            } else {
                                                                if (c === "S") {
                                                                    return "%02d".sprintf(tm_sec);
                                                                } else {
                                                                    if (c === "U") {
                                                                        _throw(new NotImplementedError("strftime format character '%s'".sprintf(c)), __py_file__, 194);
                                                                    } else {
                                                                        if (c === "w") {
                                                                            return "%d".sprintf(tm_wday + 1 % 7);
                                                                        } else {
                                                                            if (c === "W") {
                                                                                return "%d".sprintf(weekNo);
                                                                            } else {
                                                                                if (c === "x") {
                                                                                    return "%s".sprintf(date.toLocaleDateString());
                                                                                } else {
                                                                                    if (c === "X") {
                                                                                        return "%s".sprintf(date.toLocaleTimeString());
                                                                                    } else {
                                                                                        if (c === "y") {
                                                                                            return "%02d".sprintf(tm_year % 100);
                                                                                        } else {
                                                                                            if (c === "Y") {
                                                                                                return "%04d".sprintf(tm_year);
                                                                                            } else {
                                                                                                if (c === "Z") {
                                                                                                    _throw(new NotImplementedError("strftime format character '%s'".sprintf(c)), __py_file__, 208);
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            return "%" + c;
        };
        result = "";
        remainder = fmt;
        re_pct = /([^%]*)%(.)(.*)/;
        var a, fmtChar;;
        while (remainder) {
            {
                a = re_pct.exec(remainder);
                if (!a) {
                    result += remainder;
                    remainder = false;
                } else {
                    result += a[1];
                    fmtChar = a[2];
                    remainder = a[3];
                    if (typeof fmtChar != 'undefined') {
                        result += format(fmtChar);
                    }
                }
            };
        }
        return str(result);
    };
    asctime = function(t) {
        if (_isUndefined(t)) t = null;
        var t;
        if (t === null) {
            t = localtime();
        }
        return "%s %s %02d %02d:%02d:%02d %04d".sprintf(_subscript('load', _subscript('load', __c__days, 'index', t.tm_wday - 1 % 7), 'slice', null, 3, null), _subscript('load', __c__months, 'index', t.tm_mon - 1), t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_year);
    };
    ctime = function(t) {
        if (_isUndefined(t)) t = null;
        return asctime(localtime(t));
    };
    var _DATE_FORMAT_REGXES = {
        'Y': new RegExp('^-?[0-9]+'),
        'y': new RegExp('^-?[0-9]{1,2}'),
        'd': new RegExp('^[0-9]{1,2}'),
        'm': new RegExp('^[0-9]{1,2}'),
        'H': new RegExp('^[0-9]{1,2}'),
        'M': new RegExp('^[0-9]{1,2}')
    }

    /*
     * _parseData does the actual parsing job needed by `strptime`
     */

    function _parseDate(datestring, format) {
        var parsed = {};
        for (var i1 = 0, i2 = 0; i1 < format.length; i1++, i2++) {
            var c1 = format[i1];
            var c2 = datestring[i2];
            if (c1 == '%') {
                c1 = format[++i1];
                var data = _DATE_FORMAT_REGXES[c1].exec(datestring.substring(i2));
                if (!data.length) {
                    return null;
                }
                data = data[0];
                i2 += data.length - 1;
                var value = parseInt(data, 10);
                if (isNaN(value)) {
                    return null;
                }
                parsed[c1] = value;
                continue;
            }
            if (c1 != c2) {
                return null;
            }
        }
        return parsed;
    }

    /*
     * basic implementation of strptime. The only recognized formats
     * defined in _DATE_FORMAT_REGEXES (i.e. %Y, %d, %m, %H, %M)
     */

    function strptime(datestring, format) {
        var parsed = _parseDate(datestring, format);
        if (!parsed) {
            return null;
        }
        // create initial date (!!! year=0 means 1900 !!!)
        var date = new Date(0, 0, 1, 0, 0);
        date.setFullYear(0); // reset to year 0
        if (typeof parsed.Y != "undefined") {
            date.setFullYear(parsed.Y);
        }
        if (typeof parsed.y != "undefined") {
            date.setFullYear(2000 + parsed.y);
        }
        if (typeof parsed.m != "undefined") {
            if (parsed.m < 1 || parsed.m > 12) {
                return null;
            }
            // !!! month indexes start at 0 in javascript !!!
            date.setMonth(parsed.m - 1);
        }
        if (typeof parsed.d != "undefined") {
            if (parsed.m < 1 || parsed.m > 31) {
                return null;
            }
            date.setDate(parsed.d);
        }
        if (typeof parsed.H != "undefined") {
            if (parsed.H < 0 || parsed.H > 23) {
                return null;
            }
            date.setHours(parsed.H);
        }
        if (typeof parsed.M != "undefined") {
            if (parsed.M < 0 || parsed.M > 59) {
                return null;
            }
            date.setMinutes(parsed.M);
        }
        return date;
    };;
    _strptime = function(datestring, format) {
        var _ex;
        try {
            return float(strptime(datestring.valueOf(), format.valueOf()).getTime() / 1000.0);
        } catch (_ex) {
            _throw(new ValueError("Invalid or unsupported values for strptime: '%s', '%s'".sprintf(datestring, format)), __py_file__, 337);
        }
    };
    strptime = function(datestring, format) {
        var _ex, tt;
        try {
            tt = localtime(float(strptime(datestring.valueOf(), format.valueOf()).getTime() / 1000.0));
            tt.tm_isdst = -1;
            return tt;
        } catch (_ex) {
            _throw(new ValueError("Invalid or unsupported values for strptime: '%s', '%s'".sprintf(datestring, format)), __py_file__, 345);
        }
    };
    prambanan.exports('time', {
        altzone: altzone,
        asctime: asctime,
        ctime: ctime,
        d: d,
        gmtime: gmtime,
        localtime: localtime,
        mktime: mktime,
        strftime: strftime,
        strptime: strptime,
        struct_time: struct_time,
        time: time,
        timezone: timezone,
        tzname: tzname
    });
})(prambanan);
var JS, MAXYEAR, MINYEAR, NotImplementedError, TypeError, __Jan_01_0001, __builtin__, __c__days, __c__months, __import__, __py_file__, _isUndefined, _m___pyjamas__, _m_time, _strptime, _subscript, _super, _throw, date, datetime, gmtime, int, isinstance, localtime, object, strftime, t_datetime_date, t_datetime_datetime, t_datetime_time, t_datetime_timedelta, t_datetime_tzinfo, time, timedelta, tzinfo;
__builtin__ = prambanan.import('__builtin__');
TypeError = __builtin__.TypeError;
int = __builtin__.int;
__import__ = __builtin__.__import__;
object = __builtin__.object;
NotImplementedError = __builtin__.NotImplementedError;
isinstance = __builtin__.isinstance;
_super = prambanan.helpers.super;
_throw = prambanan.helpers.
throw;
_subscript = prambanan.helpers.subscript;
__py_file__ = 'datetime.py';
_isUndefined = prambanan.helpers._.isUndefined;
(function(prambanan) {
    _m___pyjamas__ = __import__('__pyjamas__');
    JS = _m___pyjamas__.JS;
    _m_time = __import__('time');
    __c__days = _m_time.__c__days;
    __c__months = _m_time.__c__months;
    strftime = _m_time.strftime;
    localtime = _m_time.localtime;
    gmtime = _m_time.gmtime;
    _strptime = _m_time._strptime;
    MINYEAR = 1;
    MAXYEAR = 1000000;
    __Jan_01_0001 = (new Date((new Date('Jan 1 1971')).getTime() - 62167132800000)).getTime();

    function t_datetime_date() {
        this.__init__.apply(this, arguments);
    }
    date = object.extend({
        constructor: t_datetime_date,
        __init__: function(year, month, day, d) {
            if (_isUndefined(d)) d = null;
            var d;
            if (d === null) {
                d = new Date(year, month - 1, day, 0, 0, 0, 0);
            }
            this._d = d;
            this.year = d.getFullYear();
            this.month = d.getMonth() + 1.0;
            this.day = d.getDate();
        },
        ctime: function() {
            return "%s %s %2d %02d:%02d:%02d %04d".sprintf(_subscript('load', _subscript('load', __c__days, 'index', this._d.getDay()), 'slice', null, 3, null), _subscript('load', _subscript('load', __c__months, 'index', this._d.getMonth()), 'slice', null, 3, null), this._d.getDate(), this._d.getHours(), this._d.getMinutes(), this._d.getSeconds(), this._d.getFullYear());
        },
        isocalendar: function() {
            var _d, isoweekday, isoweeknr, isoyear;
            isoyear = isoweeknr = isoweekday = null;
            _d = this._d;
            var gregdaynumber = function(year, month, day) {
                    var y = year;
                    var m = month;
                    if (month < 3) {
                        y--;
                        m += 12;
                    }
                    return Math.floor(365.25 * y) - Math.floor(y / 100) + Math.floor(y / 400) + Math.floor(30.6 * (m + 1)) + day - 62;
                };

            var year = _d.getFullYear();
            var month = _d.getMonth();
            var day = _d.getDate();
            var wday = _d.getDay();

            isoweekday = ((wday + 6) % 7) + 1;
            isoyear = year;

            var d0 = gregdaynumber(year, 1, 0);
            var weekday0 = ((d0 + 4) % 7) + 1;

            var d = gregdaynumber(year, month + 1, day);
            isoweeknr = Math.floor((d - d0 + weekday0 + 6) / 7) - Math.floor((weekday0 + 3) / 7);

            if ((month == 11) && ((day - isoweekday) > 27)) {
                isoweeknr = 1;
                isoyear = isoyear + 1;
            }

            if ((month == 0) && ((isoweekday - day) > 3)) {
                d0 = gregdaynumber(year - 1, 1, 0);
                weekday0 = ((d0 + 4) % 7) + 1;
                isoweeknr = Math.floor((d - d0 + weekday0 + 6) / 7) - Math.floor((weekday0 + 3) / 7);
                isoyear--;
            };
            return [isoyear, isoweeknr, isoweekday];
        },
        isoformat: function() {
            return "%04d-%02d-%02d".sprintf(this.year, this.month, this.day);
        },
        isoweekday: function() {
            return this._d.getDay() + 6 % 7 + 1;
        },
        replace: function(year, month, day) {
            if (_isUndefined(year)) year = null;
            if (_isUndefined(month)) month = null;
            if (_isUndefined(day)) day = null;
            var day, month, year;
            if (year === null) {
                year = this.year;
            }
            if (month === null) {
                month = this.month;
            }
            if (day === null) {
                day = this.day;
            }
            return new date(year, month, day);
        },
        strftime: function(format) {
            return strftime(format, this.timetuple());
        },
        timetuple: function() {
            var tm;
            tm = localtime(int(this._d.getTime() / 1000.0));
            tm.tm_hour = tm.tm_min = tm.tm_sec = 0;
            return tm;
        },
        toordinal: function() {
            return 1 + int(this._d.getTime() - __Jan_01_0001 / 86400000.0);
        },
        weekday: function() {
            return this._d.getDay() + 6 % 7;
        },
        __str__: function() {
            return this.isoformat();
        },
        __cmp__: function(other) {
            var a, b;
            if (isinstance(other, date) || isinstance(other, datetime)) {
                a = this._d.getTime();
                b = other._d.getTime();
                if (a < b) {
                    return -1;
                } else {
                    if (a === b) {
                        return 0;
                    }
                }
            } else {
                _throw(new TypeError("expected date or datetime object"), __py_file__, 123);
            }
            return 1;
        },
        __add__: function(other) {
            if (isinstance(other, timedelta)) {
                return new date(this.year, this.month, this.day + other.days);
            } else {
                _throw(new TypeError("expected timedelta object"), __py_file__, 130);
            }
        },
        __sub__: function(other) {
            var diff;
            if (isinstance(other, date) || isinstance(other, datetime)) {
                diff = this._d.getTime() - other._d.getTime();
                return new timedelta(int(diff / 86400000.0), int(diff / 1000.0) % 86400);
            } else {
                if (isinstance(other, timedelta)) {
                    return new date(this.year, this.month, this.day - other.days);
                } else {
                    _throw(new TypeError("expected date or datetime object"), __py_file__, 139);
                }
            }
        } /* static methods */
        today: function() {
            return new date(0, 0, 0, new Date());
        },
        fromtimestamp: function(timestamp) {
            var d;
            d = new Date();
            d.setTime(timestamp * 1000.0);
            return new date(0, 0, 0, d);
        },
        fromordinal: function(ordinal) {
            var d, t;
            t = __Jan_01_0001 + ordinal - 1 * 86400000.0;
            d = new Date(t);
            return new date(0, 0, 0, d);
        }
    });

    function t_datetime_time() {
        this.__init__.apply(this, arguments);
    }
    time = object.extend({
        constructor: t_datetime_time,
        __init__: function(hour, minute, second, microsecond, tzinfo, d) {
            if (_isUndefined(minute)) minute = 0;
            if (_isUndefined(second)) second = 0;
            if (_isUndefined(microsecond)) microsecond = 0;
            if (_isUndefined(tzinfo)) tzinfo = null;
            if (_isUndefined(d)) d = null;
            var d;
            if (tzinfo !== null) {
                _throw(new NotImplementedError("tzinfo"), __py_file__, 145);
            }
            if (d === null) {
                d = new Date(1970, 1, 1, hour, minute, second, 0.5 + microsecond / 1000.0);
            }
            this._d = d;
            this.hour = d.getHours();
            this.minute = d.getMinutes();
            this.second = d.getSeconds();
            this.microsecond = d.getMilliseconds() * 1000.0;
            this.tzinfo = null;
        },
        dst: function() {
            _throw(new NotImplementedError("dst"), __py_file__, 156);
        },
        isoformat: function() {
            var t;
            t = "%02d:%02d:%02d".sprintf(this.hour, this.minute, this.second);
            if (this.microsecond) {
                t += ".%06d".sprintf(this.microsecond);
            }
            return t;
        },
        replace: function(hour, minute, second, microsecond, tzinfo) {
            if (_isUndefined(hour)) hour = null;
            if (_isUndefined(minute)) minute = null;
            if (_isUndefined(second)) second = null;
            if (_isUndefined(microsecond)) microsecond = null;
            if (_isUndefined(tzinfo)) tzinfo = null;
            var hour, microsecond, minute, second;
            if (tzinfo !== null) {
                _throw(new NotImplementedError("tzinfo"), __py_file__, 166);
            }
            if (hour === null) {
                hour = this.hour;
            }
            if (minute === null) {
                minute = this.minute;
            }
            if (second === null) {
                second = this.second;
            }
            if (microsecond === null) {
                microsecond = this.microsecond;
            }
            return new time(hour, minute, second, microsecond);
        },
        strftime: function(format) {
            return strftime(format, localtime(int(this._d.getTime() / 1000.0)));
        },
        tzname: function() {
            return null;
        },
        utcoffset: function() {
            return null;
        },
        __str__: function() {
            return this.isoformat();
        } /* static methods */
    });

    function t_datetime_datetime() {
        this.__init__.apply(this, arguments);
    }
    datetime = date.extend({
        constructor: t_datetime_datetime,
        __init__: function(year, month, day, hour, minute, second, microsecond, tzinfo, d) {
            if (_isUndefined(hour)) hour = 0;
            if (_isUndefined(minute)) minute = 0;
            if (_isUndefined(second)) second = 0;
            if (_isUndefined(microsecond)) microsecond = 0;
            if (_isUndefined(tzinfo)) tzinfo = null;
            if (_isUndefined(d)) d = null;
            var d;
            if (d === null) {
                d = new Date(year, month - 1, day, hour, minute, second, 0.5 + microsecond / 1000.0);
            }
            _super(this, '__init__')(0, 0, 0, d);
            this.hour = d.getHours();
            this.minute = d.getMinutes();
            this.second = d.getSeconds();
            this.microsecond = d.getMilliseconds() * 1000.0;
            this.tzinfo = null;
        },
        timetuple: function() {
            return localtime(int(this._d.getTime() / 1000.0));
        },
        astimezone: function(tz) {
            _throw(new NotImplementedError("astimezone"), __py_file__, 243);
        },
        date: function() {
            return new date(this.year, this.month, this.day);
        },
        time: function() {
            return new time(this.hour, this.minute, this.second, this.microsecond);
        },
        replace: function(year, month, day, hour, minute, second, microsecond, tzinfo) {
            if (_isUndefined(year)) year = null;
            if (_isUndefined(month)) month = null;
            if (_isUndefined(day)) day = null;
            if (_isUndefined(hour)) hour = null;
            if (_isUndefined(minute)) minute = null;
            if (_isUndefined(second)) second = null;
            if (_isUndefined(microsecond)) microsecond = null;
            if (_isUndefined(tzinfo)) tzinfo = null;
            var day, hour, microsecond, minute, month, second, year;
            if (tzinfo !== null) {
                _throw(new NotImplementedError("tzinfo"), __py_file__, 253);
            }
            if (year === null) {
                year = this.year;
            }
            if (month === null) {
                month = this.month;
            }
            if (day === null) {
                day = this.day;
            }
            if (hour === null) {
                hour = this.hour;
            }
            if (minute === null) {
                minute = this.minute;
            }
            if (second === null) {
                second = this.second;
            }
            if (microsecond === null) {
                microsecond = this.microsecond;
            }
            return new datetime(year, month, day, hour, minute, second, microsecond);
        },
        timetz: function() {
            _throw(new NotImplementedError("timetz"), __py_file__, 271);
        },
        utctimetuple: function() {
            return gmtime(this._d.getTime() / 1000.0);
        },
        isoformat: function(sep) {
            if (_isUndefined(sep)) sep = "T";
            var t;
            t = "%04d-%02d-%02d%s%02d:%02d:%02d".sprintf(this.year, this.month, this.day, sep, this.hour, this.minute, this.second);
            if (this.microsecond) {
                t += ".%06d".sprintf(this.microsecond);
            }
            return t;
        },
        __add__: function(other) {
            var d, day, hour, microsecond, minute, month, second, year;
            if (isinstance(other, timedelta)) {
                year = this.year;
                month = this.month;
                day = this.day + other.days;
                hour = this.hour + other.seconds / 3600.0;
                minute = this.minute + other.seconds / 60.0 % 60;
                second = this.second + other.seconds % 60;
                microsecond = this.microsecond + other.microseconds;
                d = new Date(year, month, day, hour, minute, second, microsecond);
                return new datetime(0, 0, 0, 0, 0, 0, 0, null, d);
            } else {
                _throw(new TypeError("expected timedelta object"), __py_file__, 294);
            }
        },
        __sub__: function(other) {
            var d, day, diff, hour, microsecond, minute, month, second, year;
            if (isinstance(other, date) || isinstance(other, datetime)) {
                diff = this._d.getTime() - other._d.getTime();
                return new timedelta(int(diff / 86400000.0), int(diff / 1000.0) % 86400);
            } else {
                if (isinstance(other, timedelta)) {
                    year = this.year;
                    month = this.month;
                    day = this.day - other.days;
                    hour = this.hour - other.seconds / 3600.0;
                    minute = this.minute - other.seconds / 60.0 % 60;
                    second = this.second - other.seconds % 60;
                    microsecond = this.microsecond - other.microseconds;
                    d = new Date(year, month, day, hour, minute, second, microsecond);
                    return new datetime(0, 0, 0, 0, 0, 0, 0, null, d);
                } else {
                    _throw(new TypeError("expected date or datetime object"), __py_file__, 312);
                }
            }
        },
        __str__: function() {
            return this.isoformat(" ");
        } /* static methods */
        combine: function(date, time) {
            return new datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, time.microsecond);
        },
        fromtimestamp: function(timestamp, tz) {
            if (_isUndefined(tz)) tz = null;
            var d;
            if (tz !== null) {
                _throw(new NotImplementedError("tz"), __py_file__, 208);
            }
            d = new Date();
            d.setTime(timestamp * 1000.0);
            return new datetime(0, 0, 0, 0, 0, 0, 0, null, d);
        },
        fromordinal: function(ordinal) {
            var d;
            d = new Date();
            d.setTime(ordinal - 719163.0 * 86400000.0);
            return new datetime(0, 0, 0, 0, 0, 0, 0, null, d);
        },
        now: function(tz) {
            if (_isUndefined(tz)) tz = null;
            if (tz !== null) {
                _throw(new NotImplementedError("tz"), __py_file__, 222);
            }
            return new datetime(0, 0, 0, 0, 0, 0, 0, null, new Date());
        },
        strptime: function(datestring, format) {
            return datetime.fromtimestamp(_strptime(datestring, format));
        },
        utcfromtimestamp: function(timestamp) {
            var tm;
            tm = gmtime(timestamp);
            return new datetime(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
        },
        utcnow: function() {
            var d;
            d = new Date();
            return datetime.utcfromtimestamp(int(d.getTime() / 1000.0));
        }
    });

    function t_datetime_timedelta() {
        this.__init__.apply(this, arguments);
    }
    timedelta = object.extend({
        constructor: t_datetime_timedelta,
        __init__: function(days, seconds, microseconds, milliseconds, minutes, hours, weeks) {
            if (_isUndefined(days)) days = 0;
            if (_isUndefined(seconds)) seconds = 0;
            if (_isUndefined(microseconds)) microseconds = 0;
            if (_isUndefined(milliseconds)) milliseconds = 0;
            if (_isUndefined(minutes)) minutes = 0;
            if (_isUndefined(hours)) hours = 0;
            if (_isUndefined(weeks)) weeks = 0;
            this.days = weeks * 7.0 + days;
            this.seconds = hours * 3600.0 + minutes * 60.0 + seconds;
            this.microseconds = milliseconds * 1000.0 + microseconds;
        } /* static methods */
    });

    function t_datetime_tzinfo() {
        this.__init__.apply(this, arguments);
    }
    tzinfo = object.extend({
        constructor: t_datetime_tzinfo /* pass */
        /* static methods */
    });
    date.min = new date(1, 1, 1);
    date.max = new date(9999, 12, 31);
    date.resolution = new timedelta(1);
    time.min = new time(0, 0);
    time.max = new time(23, 59, 59, 999999);
    time.resolution = new timedelta(0, 0, 1);
    datetime.min = new datetime(1, 1, 1, 0, 0);
    datetime.max = new datetime(9999, 12, 31, 23, 59, 59, 999999);
    datetime.resolution = new timedelta(0, 0, 1);
    timedelta.min = new timedelta(-999999999);
    timedelta.max = new timedelta(999999999);
    timedelta.resolution = new timedelta(0, 0, 1);
    prambanan.exports('datetime', {
        MAXYEAR: MAXYEAR,
        MINYEAR: MINYEAR,
        date: date,
        datetime: datetime,
        time: time,
        timedelta: timedelta,
        tzinfo: tzinfo
    });
})(prambanan);