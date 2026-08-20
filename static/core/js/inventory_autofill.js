(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Auto-number quote line items
        function updateLineNumbers() {
            const $rows = $('#id_quotelineitem_set-group .dynamic-quotelineitem_set');
            let counter = 1;
            $rows.each(function() {
                const $row = $(this);
                // Skip rows marked for deletion
                if ($row.find('input[name$="-DELETE"]').is(':checked')) {
                    return;
                }
                // Update line number display
                const $lineNumCell = $row.find('td:first');
                if ($lineNumCell.length) {
                    $lineNumCell.text(counter);
                }
                counter++;
            });
        }
        
        // Initial numbering
        setTimeout(updateLineNumbers, 100);
        
        // Update numbering when rows are added/removed
        $(document).on('formset:added', updateLineNumbers);
        $(document).on('formset:removed', updateLineNumbers);
        $(document).on('change', 'input[name$="-DELETE"]', updateLineNumbers);
        
        // Handle inventory item selection change
        $(document).on('change', 'select[name$="-inventory_item"]', function() {
            const $row = $(this).closest('tr');
            const inventoryId = $(this).val();
            
            if (!inventoryId) {
                // Clear fields if no inventory item selected
                $row.find('input[name$="-description"]').val('');
                $row.find('input[name$="-unit"]').val('unit');
                $row.find('input[name$="-unit_price"]').val('0.00');
                return;
            }
            
            // Get inventory item data via AJAX
            $.ajax({
                url: '/admin/core/inventoryitem/' + inventoryId + '/json/',
                method: 'GET',
                dataType: 'json',
                success: function(data) {
                    // Auto-populate fields
                    $row.find('input[name$="-description"]').val(data.description);
                    $row.find('input[name$="-unit"]').val(data.unit);
                    $row.find('input[name$="-unit_price"]').val(data.unit_price);
                    
                    // Trigger change event to update totals
                    $row.find('input[name$="-unit_price"]').trigger('change');
                },
                error: function() {
                    console.error('Failed to fetch inventory item data');
                }
            });
        });
    });
})(django.jQuery);
