// Generated by CoffeeScript 1.7.1
(function() {
  this.VendorInfo = (function() {
    function VendorInfo(vendor) {
      var attr, list, _i, _len, _ref;
      this.dom = $('<div class="vendor-info-box">');
      this.dom.append($('<h3>').text(gettext('Vendor')));
      list = $('<dl class="dl-horizontal">');
      _ref = ['name', 'email', 'phone', 'id'];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        attr = _ref[_i];
        list.append($('<dt>').text(attr));
        list.append($('<dd>').text(vendor[attr]));
      }
      this.dom.append(list);
    }

    VendorInfo.prototype.render = function() {
      return this.dom;
    };

    return VendorInfo;

  })();

}).call(this);
