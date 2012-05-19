(function (prambanan) {
    var Anu, Anu2, Anu3, Anu5, Anu6, Anuu, __builtin__, __import__, _class, colander, object;
    __builtin__ = prambanan.import('__builtin__');
    __import__ = __builtin__.__import__;
    object = __builtin__.object;
    _class = prambanan.helpers.class;
    colander = __import__('colander');

    function t__Anu_() {
        this.__init__.apply(this, arguments);
    }
    Anu = _class(t__Anu_, [object], function () { /* pass */
        return [{}, {}, {}]
    });

    function t__Anuu_() {
        this.__init__.apply(this, arguments);
    }
    Anuu = _class(t__Anuu_, [object], function () {
        var anu;
        lala = 3;
        anu = function (self) {
            var self;
            self = this;
            self.anu = 4;
        };
        return [{anu: anu}, {}, {}]
    });

    function t__Anu2_() {
        this.__init__.apply(this, arguments);
    }
    Anu2 = _class(t__Anu2_, [object], function () {
        var anu, anu3;
        anu = function (self) {
            self.anu = 4;
        };
        anu = anu;
        anu3 = function (self) {
            self.anu = 4;
        };
        anu3 = anu3;
        return [{}, {anu: anu,anu3: anu3}, {}]
    });

    function t__Anu3_() {
        this.__init__.apply(this, arguments);
    }
    Anu3 = _class(t__Anu3_, [Anu, Anu2], function () {
        var anu, anu3;
        lala = 3;
        anu = function (self) {
            var self;
            self = this;
            self.anu = 4;
        };
        anu3 = function (self) {
            self.anu = 4;
        };
        anu3 = anu3;
        return [{anu: anu}, {anu3: anu3}, {}]
    });

    function t__Anu5_() {
        this.__init__.apply(this, arguments);
    }
    Anu5 = _class(t__Anu5_, [Anu, Anu2], function () {
        var anu, anu3;
        lala = 3;
        anu = function (self) {
            var self;
            self = this;
            self.anu = 4;
        };
        anu3 = function (self) {
            self.anu = 4;
        };
        anu3 = anu3;
        return [{anu: anu}, {anu3: anu3}, {}]
    });

    function t__Anu6_() {
        this.__init__.apply(this, arguments);
    }
    Anu6 = _class(t__Anu6_, [Anu, Anu2, Anu5], function () {
        var anu, anu3;
        anu3 = function (self) {
            self.anu = 4;
        };
        anu3 = anu3;
        lala = 3;
        anu = function (self) {
            var self;
            self = this;
            self.anu = 4;
        };
        return [{anu: anu}, {anu3: anu3}, {}]
    });
    prambanan.exports('', {Anu: Anu,Anu2: Anu2,Anu3: Anu3,Anu5: Anu5,Anu6: Anu6,Anuu: Anuu});
})(prambanan);