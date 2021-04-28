This module change the behavior or RMA creation in order to assign multiple RMAs
for a same partner to a same procurement group. This way, the products replaced or returned will be grouped
in a same delivery order.
An index is added in each RMA name and incremented for each grouped RMA. For example, if we create 2 RMAs for the same partner/delivery address
we will have RMA0001-1 and RMA0001-2, both linked to a group named RMA0001.
If both products are replaced, both will appear in a delivery order with RMA0001 as origin.

The grouping is only done at RMA creation and the new RMA will only be grouped with a draft/new RMA
