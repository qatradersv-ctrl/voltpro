/**
 * Quote Line Items - Dynamic Calculations
 * Handles real-time line total calculations and form enhancements
 */
(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initQuoteLineItems();
    });

    function initQuoteLineItems() {
        const lineItemsFormset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
        if (!lineItemsFormset) return;

        // Add event listeners for dynamic calculations
        addCalculationListeners();
        
        // Add add/remove row listeners
        addFormsetListeners();
        
        // Initial calculation
        calculateAllLineTotals();
    }

    function addCalculationListeners() {
        const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
        if (!formset) return;

        // Listen for input changes on quantity and unit price fields
        formset.addEventListener('input', function(e) {
            if (e.target.matches('input[name$="-quantity"]') || 
                e.target.matches('input[name$="-unit_price"]')) {
                const row = e.target.closest('tr');
                if (row) {
                    calculateLineTotal(row);
                }
            }
        });

        // Listen for row additions
        formset.addEventListener('DOMNodeInserted', function(e) {
            if (e.target.matches('tr.form-row') || e.target.closest('tr.form-row')) {
                const row = e.target.matches('tr.form-row') ? e.target : e.target.closest('tr.form-row');
                addRowCalculationListener(row);
            }
        });
    }

    function addRowCalculationListener(row) {
        const quantityInput = row.querySelector('input[name$="-quantity"]');
        const unitPriceInput = row.querySelector('input[name$="-unit_price"]');

        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                calculateLineTotal(row);
            });
        }

        if (unitPriceInput) {
            unitPriceInput.addEventListener('input', function() {
                calculateLineTotal(row);
            });
        }
    }

    function calculateLineTotal(row) {
        const quantityInput = row.querySelector('input[name$="-quantity"]');
        const unitPriceInput = row.querySelector('input[name$="-unit_price"]');
        const lineTotalDisplay = row.querySelector('.field-line_total_display p');

        if (!quantityInput || !unitPriceInput || !lineTotalDisplay) return;

        const quantity = parseFloat(quantityInput.value) || 0;
        const unitPrice = parseFloat(unitPriceInput.value) || 0;
        const lineTotal = quantity * unitPrice;

        // Format as currency
        lineTotalDisplay.textContent = formatCurrency(lineTotal);
        
        // Add visual feedback
        if (lineTotal > 0) {
            lineTotalDisplay.style.color = '#1C8A5F';
            lineTotalDisplay.style.fontWeight = '700';
        } else {
            lineTotalDisplay.style.color = '#6B7280';
            lineTotalDisplay.style.fontWeight = '500';
        }
    }

    function calculateAllLineTotals() {
        const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
        if (!formset) return;

        const rows = formset.querySelectorAll('tr.form-row:not(.empty-form)');
        rows.forEach(row => {
            calculateLineTotal(row);
        });
    }

    function formatCurrency(amount) {
        return 'KES ' + amount.toLocaleString('en-KE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function addFormsetListeners() {
        const addButtons = document.querySelectorAll('.add-row a');
        addButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Delay to allow Django to add the row
                setTimeout(() => {
                    const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
                    if (formset) {
                        const newRows = formset.querySelectorAll('tr.form-row:not(.empty-form)');
                        const lastRow = newRows[newRows.length - 1];
                        if (lastRow) {
                            addRowCalculationListener(lastRow);
                            
                            // Set default values
                            const quantityInput = lastRow.querySelector('input[name$="-quantity"]');
                            const unitInput = lastRow.querySelector('input[name$="-unit"]');
                            
                            if (quantityInput) quantityInput.value = '1.00';
                            if (unitInput) unitInput.value = 'unit';
                        }
                    }
                }, 100);
            });
        });

        // Add listeners for delete buttons
        const deleteButtons = document.querySelectorAll('.inline-deletelink, .delete a');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                if (row) {
                    // Visual feedback before deletion
                    row.style.opacity = '0.5';
                    row.style.background = '#FEF2F2';
                }
            });
        });
    }

    // Enhance the form with additional UX improvements
    function enhanceLineItemsForm() {
        const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
        if (!formset) return;

        // Add tooltips to help text
        const helpIcons = formset.querySelectorAll('.help-tooltip');
        helpIcons.forEach(icon => {
            icon.style.cursor = 'help';
            icon.style.marginLeft = '4px';
        });

        // Improve description field placeholder
        const descriptionInputs = formset.querySelectorAll('input[name$="-description"]');
        descriptionInputs.forEach(input => {
            input.placeholder = 'Enter item description...';
        });

        // Improve unit field suggestions
        const unitInputs = formset.querySelectorAll('input[name$="-unit"]');
        const commonUnits = ['unit', 'hrs', 'm', 'lot', 'kg', 'pcs', 'sqm', 'lm'];
        
        unitInputs.forEach(input => {
            input.setAttribute('list', 'common-units');
        });

        // Create datalist if it doesn't exist
        if (!document.getElementById('common-units')) {
            const datalist = document.createElement('datalist');
            datalist.id = 'common-units';
            commonUnits.forEach(unit => {
                const option = document.createElement('option');
                option.value = unit;
                datalist.appendChild(option);
            });
            document.body.appendChild(datalist);
        }
    }

    // Initialize enhancements
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhanceLineItemsForm);
    } else {
        enhanceLineItemsForm();
    }

})();