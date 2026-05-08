/**
 * initDynamicLines — reusable add/remove line-item table.
 *
 * config = {
 *   addBtnId:       id of the "Add Line" button
 *   linesBodyId:    id of the <tbody> to append rows into
 *   selectClass:    CSS class of the product/material <select>
 *   priceFieldClass: CSS class of the price <input> in the same row
 * }
 */
function initDynamicLines(config) {
  var rowTemplate = document.querySelector('.line-row').outerHTML;

  document.getElementById(config.addBtnId).addEventListener('click', function () {
    document.getElementById(config.linesBodyId).insertAdjacentHTML('beforeend', rowTemplate);
    attachHandlers();
  });

  function attachHandlers() {
    document.querySelectorAll('.' + config.selectClass).forEach(function (sel) {
      sel.onchange = function () {
        var opt = this.options[this.selectedIndex];
        var price = opt.dataset.price || '';
        this.closest('tr').querySelector('.' + config.priceFieldClass).value = price;
      };
    });

    document.querySelectorAll('.remove-line').forEach(function (btn) {
      btn.onclick = function () {
        if (document.querySelectorAll('.line-row').length > 1) {
          this.closest('tr').remove();
        }
      };
    });
  }

  attachHandlers();
}
