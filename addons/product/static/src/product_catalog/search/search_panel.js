import { onWillStart, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useBus } from "@web/core/utils/hooks";
import { SearchPanel } from "@web/search/search_panel/search_panel";

export class ProductCatalogSearchPanel extends SearchPanel {
    static template = "ProductCatalog.SearchPanel";
    static subTemplates = {
        ...SearchPanel.subTemplates,
        filtersGroup: "ProductCatalogSearchPanel.FiltersGroup",
    };

    setup() {
        super.setup();
        this.state = useState({
            ...this.state,
            sectionOfTags: {},
            sectionOfSections: new Map(),
            isAddingSection: false,
            newSectionName: "",
        });
        this.onDrop = this.onDrop.bind(this);

        useBus(this.env.searchModel, "section-line-count-change", this.updateSectionLineCount);

        onWillStart(async () => {
            await this.loadSections();
        })
    }

    get isNonMrpOrderActive() {
        return (
            this.env.model.config.context.product_catalog_order_model !== 'mrp.production'
            && this.env.model.config.context.product_catalog_order_id
        );
    }

    get selectedSection() {
        return this.env.searchModel.selectedSection;
    }

    updateActiveValues() {
        super.updateActiveValues();
        this.state.sectionOfTags = this.buildSectionOfTags();
    }

    buildSectionOfTags() {
        const values = this.env.searchModel.filters[0].values;
        let sections = new Map();

        values.forEach(element => {
            const name = element.display_name;
            const id = element.id;
            const count = element.__count;
            if (sections.has(name)) {
                let currentTag = sections.get(name);
                currentTag.get('ids').push(id);
                currentTag.set('count', currentTag.get('count') + count);
            } else if (count > 0) {
                let newTag = new Map();
                newTag.set('ids', [id]);
                newTag.set('count', count);
                sections.set(name, newTag);
            }
        });

        return sections;
    }

    toggleTagFilterValue(filterId, tagIds, { currentTarget }) {
        tagIds.forEach(id => {
            this.toggleFilterValue(filterId, id, { currentTarget });
        })
    }

    enableSectionInput() {
        this.state.isAddingSection = true;
        setTimeout(() => document.querySelector('.o_section_input')?.focus(), 100);
    }

    onDragStart(sectionId, ev) {
        ev.dataTransfer.setData("text/plain", sectionId);
    }

    onDragOver(ev) {
        ev.preventDefault();
    }

    onDrop(targetSecId, ev) {
        ev.preventDefault();
        const moveSecId = ev.dataTransfer.getData("text/plain");
        if (moveSecId !== targetSecId) this.reorderSections(moveSecId, targetSecId);
    }

    onSectionInputKeydown(event) {
        if (event.key === "Enter") {
            this.createSection();
        } else if (event.key === "Escape") {
            this.state.isAddingSection = false;
            this.state.newSectionName = "";
        }
    }

    setSelectedSection(sectionId=null, filtered=false) {
        this.env.searchModel.setSelectedSection(sectionId, filtered);
    }

    async createSection() {
        const sectionName = this.state.newSectionName.trim();
        if (!sectionName) return this.state.isAddingSection = false;

        const section = await rpc("/product/catalog/create_section", {
            res_model: this.env.model.config.context.product_catalog_order_model,
            order_id: this.env.model.config.context.order_id,
            section_name: sectionName,
        });

        if (section?.id) {
            this.state.sectionOfSections.set(section.id, {
                name: section.name,
                sequence: section.sequence,
                line_count: 0,
            });
            this.setSelectedSection(section.id);
        }
        this.state.isAddingSection = false;
        this.state.newSectionName = "";
    }

    async loadSections() {
        if (!this.isNonMrpOrderActive) return;
        const sections = await rpc(
            "/product/catalog/get_sections", {
            res_model: this.env.model.config.context.product_catalog_order_model,
            order_id: this.env.model.config.context.order_id,
            child_field: this.env.model.config.context.child_field,
        });

        const sectionMap = this.state.sectionOfSections || new Map();
        for (const {id, name, sequence, line_count} of sections) {
            const existingSection = sectionMap.get(id);
            if (!existingSection) {
                sectionMap.set(id, {name, sequence, line_count});
            }
        }
        this.state.sectionOfSections = sectionMap;
    }

    async reorderSections(moveId, targetId) {
        [moveId, targetId] = [Number(moveId), Number(targetId)];
        const sections = this.state.sectionOfSections;
        const moveSection = sections.get(moveId);
        const targetSection = sections.get(targetId);

        if (!moveSection || !targetSection) return;

        const updatedSequences = await rpc("/product/catalog/resequence_sections", {
            res_model: this.env.model.config.context.product_catalog_order_model,
            order_id: this.env.model.config.context.order_id,
            child_field: this.env.model.config.context.child_field,
            sections: [
                { id: moveId, sequence: moveSection.sequence },
                { id: targetId, sequence: targetSection.sequence },
            ],
        });
        for (const [id, sequence] of Object.entries(updatedSequences)) {
            const section = sections.get(Number(id));
            if (section) {
                section.sequence = sequence;
            }
        }
        this.state.sectionOfSections = new Map(
            [...sections].sort((a, b) => a[1].sequence - b[1].sequence)
        );
    }

    updateSectionLineCount(event) {
        const {sectionId, lineCountChange} = event.detail;
        const section = this.state.sectionOfSections.get(sectionId);
        if (section) {
            section.line_count = Math.max(0, section.line_count + lineCountChange);
        }
    }
}
