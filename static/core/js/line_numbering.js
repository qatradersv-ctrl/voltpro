(function($) {
    $(document).ready(function() {
        // Function to add line numbers to Quote Line Items table
        function addLineNumbers() {
            // Find the Quote Line Items table
            var table = $('.inline-group.tabular table').first();
            if (table.length === 0) return;
            
            var thead = table.find('thead tr');
            var tbody = table.find('tbody');
            
            // Hide the original column (Django's hidden ID column)
            thead.find('th.original').hide();
            tbody.find('td.original').hide();
            
            // Add header cell for line numbers if it doesn't exist
            if (!thead.find('th.line-number-header').length) {
                thead.prepend('<th class="line-number-header" style="width: 50px; text-align: center;">#</th>');
            }
            
            // Add line number cells to each row
            tbody.find('tr').not('.empty-form').each(function(index) {
                var row = $(this);
                if (!row.find('td.line-number-cell').length) {
                    row.prepend('<td class="line-number-cell" style="text-align: center; vertical-align: middle; font-weight: 600; color: #2c3e50;">' + (index + 1) + '</td>');
                } else {
                    row.find('td.line-number-cell').text(index + 1);
                }
            });
            
            // Ensure empty form has line number cell (hidden)
            tbody.find('tr.empty-form').each(function() {
                var row = $(this);
                if (!row.find('td.line-number-cell').length) {
                    row.prepend('<td class="line-number-cell" style="display: none;"></td>');
                }
            });
        }
        
        // Initial numbering
        addLineNumbers();
        
        // Re-number when inline rows are added or removed
        $(document).on('formset:added', function(event, row) {
            addLineNumbers();
        });
        
        $(document).on('formset:removed', function(event, row) {
            addLineNumbers();
        });
        
        // Also observe DOM changes for dynamic updates
        var observer = new MutationObserver(function(mutations) {
            addLineNumbers();
        });
        
        var table = $('.inline-group.tabular table').first();
        if (table.length) {
            observer.observe(table.find('tbody')[0], {
                childList: true,
                subtree: true
            });
        }
    });
})(django.jQuery);
