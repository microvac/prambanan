(function(prambanan) {
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
            if (d === null) d = new Date(year, month - 1, day, 0, 0, 0, 0);
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
            if (year === null) year = this.year;
            if (month === null) month = this.month;
            if (day === null) day = this.day;
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
                if (a < b) return -1;
                else if (a === b) return 0;
            }
            else_throw(new TypeError("expected date or datetime object"), __py_file__, 123);
            return 1;
        },
        __add__: function(other) {
            if (isinstance(other, timedelta)) return new date(this.year, this.month, this.day + other.days);
            else_throw(new TypeError("expected timedelta object"), __py_file__, 130);
        },
        __sub__: function(other) {
            var diff;
            if (isinstance(other, date) || isinstance(other, datetime)) {
                diff = this._d.getTime() - other._d.getTime();
                return new timedelta(int(diff / 86400000.0), int(diff / 1000.0) % 86400);
            } else if (isinstance(other, timedelta)) return new date(this.year, this.month, this.day - other.days);
            else_throw(new TypeError("expected date or datetime object"), __py_file__, 139);
        }
    }, { /* static methods */
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
            if (tzinfo !== null) _throw(new NotImplementedError("tzinfo"), __py_file__, 145);
            if (d === null) d = new Date(1970, 1, 1, hour, minute, second, 0.5 + microsecond / 1000.0);
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
            if (this.microsecond) t += ".%06d".sprintf(this.microsecond);
            return t;
        },
        replace: function(hour, minute, second, microsecond, tzinfo) {
            if (_isUndefined(hour)) hour = null;
            if (_isUndefined(minute)) minute = null;
            if (_isUndefined(second)) second = null;
            if (_isUndefined(microsecond)) microsecond = null;
            if (_isUndefined(tzinfo)) tzinfo = null;
            if (tzinfo !== null) _throw(new NotImplementedError("tzinfo"), __py_file__, 166);
            if (hour === null) hour = this.hour;
            if (minute === null) minute = this.minute;
            if (second === null) second = this.second;
            if (microsecond === null) microsecond = this.microsecond;
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
        }
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
            if (d === null) d = new Date(year, month - 1, day, hour, minute, second, 0.5 + microsecond / 1000.0);
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
            if (tzinfo !== null) _throw(new NotImplementedError("tzinfo"), __py_file__, 253);
            if (year === null) year = this.year;
            if (month === null) month = this.month;
            if (day === null) day = this.day;
            if (hour === null) hour = this.hour;
            if (minute === null) minute = this.minute;
            if (second === null) second = this.second;
            if (microsecond === null) microsecond = this.microsecond;
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
            if (this.microsecond) t += ".%06d".sprintf(this.microsecond);
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
            }
            else_throw(new TypeError("expected timedelta object"), __py_file__, 294);
        },
        __sub__: function(other) {
            var d, day, diff, hour, microsecond, minute, month, second, year;
            if (isinstance(other, date) || isinstance(other, datetime)) {
                diff = this._d.getTime() - other._d.getTime();
                return new timedelta(int(diff / 86400000.0), int(diff / 1000.0) % 86400);
            } else if (isinstance(other, timedelta)) {
                year = this.year;
                month = this.month;
                day = this.day - other.days;
                hour = this.hour - other.seconds / 3600.0;
                minute = this.minute - other.seconds / 60.0 % 60;
                second = this.second - other.seconds % 60;
                microsecond = this.microsecond - other.microseconds;
                d = new Date(year, month, day, hour, minute, second, microsecond);
                return new datetime(0, 0, 0, 0, 0, 0, 0, null, d);
            }
            else_throw(new TypeError("expected date or datetime object"), __py_file__, 312);
        },
        __str__: function() {
            return this.isoformat(" ");
        }
    }, { /* static methods */
        combine: function(date, time) {
            return new datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, time.microsecond);
        },
        fromtimestamp: function(timestamp, tz) {
            if (_isUndefined(tz)) tz = null;
            var d;
            if (tz !== null) _throw(new NotImplementedError("tz"), __py_file__, 208);
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
            if (tz !== null) _throw(new NotImplementedError("tz"), __py_file__, 222);
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
        }
    });

    function t_datetime_tzinfo() {
        this.__init__.apply(this, arguments);
    }
    tzinfo = object.extend({
        constructor: t_datetime_tzinfo /* pass */
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