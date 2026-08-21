/**
 * Quote Line Items - Dynamic Calculations (Tailwind CSS version)
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
        
        // Update styling based on value
        if (lineTotal > 0) {
            lineTotalDisplay.className = 'w-full px-3 py-2 bg-green-50 border border-green-200 rounded-md text-green-700 font-bold text-right';
        } else {
            lineTotalDisplay.className = 'w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-md text-gray-500 text-right';
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
        // Use Django's built-in formset functionality
        const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
        if (!formset) return;

        // Listen for DOM changes to detect new rows
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.matches && node.matches('tr.form-row:not(.empty-form)')) {
                            addRowCalculationListener(node);
                        } else if (node.querySelector) {
                            const rows = node.querySelectorAll('tr.form-row:not(.empty-form)');
                            rows.forEach(addRowCalculationListener);
                        }
                    });
                }
            });
        });

        observer.observe(formset, {
            childList: true,
            subtree: true
        });

        // Also handle the standard add button click as fallback
        const addButtons = document.querySelectorAll('.add-row a');
        addButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                // Let Django handle the click, then wait for row to be added
                setTimeout(() => {
                    const formset = document.querySelector('.js-inline-admin-formset[data-inline-type="tabular"]');
                    if (formset) {
                        const newRows = formset.querySelectorAll('tr.form-row:not(.empty-form)');
                        const lastRow = newRows[newRows.length - 1];
                        if (lastRow) {
                            addRowCalculationListener(lastRow);
                        }
                    }
                }, 200);
            });
        });
    }
})();
