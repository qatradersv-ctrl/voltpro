(function($) {
    'use strict';
    
    $(document).ready(function() {
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
