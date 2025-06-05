import { ProductCatalogKanbanModel } from "@product/product_catalog/kanban_model";

export class PurchaseProductCatalogKanbanModel extends ProductCatalogKanbanModel {
    async _loadData(params) {
        if (
            this.env.searchModel.selectedSection.filtered
            && params.context.product_catalog_order_model === 'purchase.order'
        ) {
            const filteredDomain = [['is_in_selected_section_of_purchase_order', '=', true]];
            params = {
                ...params,
                domain: [...(params.domain || []), ...filteredDomain],
                context: {
                    ...params.context,
                    selected_section_id: this.env.searchModel.selectedSection.sectionId,
                },
            };
        }
        return await super._loadData(params);
    }
}
