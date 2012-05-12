(function (prambanan) {
    var Anu, Anu2, Anu3, Anu5, Anu6, Anuu, __builtin__, _extend, object, t__Anu2_, t__Anu3_, t__Anu5_, t__Anu6_, t__Anu_, t__Anuu_;
    __builtin__ = prambanan.import('__builtin__');
    object = __builtin__.object;
    _extend = prambanan.helpers.extend;

    function t__Anu_() {
        this.__init__.apply(this, arguments);
    }
    Anu = _extend([object], t__Anu_, { /* pass */
    });

    function t__Anuu_() {
        this.__init__.apply(this, arguments);
    }
    Anuu = _extend([object], t__Anuu_, {
        lala: 3,
        anu: function () {
            var self;
            self = this;
            self.anu = 4;
        }
    });

    function t__Anu2_() {
        this.__init__.apply(this, arguments);
    }
    Anu2 = _extend([object], t__Anu2_, {
        lala: 3,
        anu: function () {
            var self;
            self = this;
            self.anu = 4;
        } /* static methods */
    }, {
        anu3: function (self) {
            self.anu = 4;
        }
    });

    function t__Anu3_() {
        this.__init__.apply(this, arguments);
    }
    Anu3 = _extend([Anu, Anu2], t__Anu3_, {
        lala: 3,
        anu: function () {
            var self;
            self = this;
            self.anu = 4;
        } /* static methods */
    }, {
        anu3: function (self) {
            self.anu = 4;
        }
    });
    /**
     * tada da da
     */

    function t__Anu5_() {
        this.__init__.apply(this, arguments);
    }
    Anu5 = _extend([Anu, Anu2], t__Anu5_, {
        lala: 3,
        anu: function () {
            var self;
            self = this;
            self.anu = 4;
        } /* static methods */
    }, {
        anu3: function (self) {
            self.anu = 4;
        }
    });
    /**
     * tada da da
     */

    function t__Anu6_() {
        this.__init__.apply(this, arguments);
    }
    Anu6 = _extend([Anu, Anu2, Anu5], t__Anu6_, {
        lala: 3,
        anu: function () {
            var self;
            self = this;
            self.anu = 4;
        } /* static methods */
    }, {
        anu3: function (self) {
            self.anu = 4;
        }
    });
    prambanan.exports('', {
        Anu: Anu,
        Anu2: Anu2,
        Anu3: Anu3,
        Anu5: Anu5,
        Anu6: Anu6,
        Anuu: Anuu
    });
})(prambanan);