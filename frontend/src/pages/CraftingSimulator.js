var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { craftingApi } from '@/services/crafting-api';
import { getCurrencyDescription, getOmenDescription } from '@/data/currency-descriptions';
import './CraftingSimulator.css';
function CraftingSimulator() {
    const [item, setItem] = useState({
        base_name: "Int Armour Body Armour",
        base_category: 'int_armour',
        rarity: 'Normal',
        item_level: 65,
        quality: 20,
        implicit_mods: [],
        prefix_mods: [],
        suffix_mods: [],
        corrupted: false,
        base_stats: {},
        calculated_stats: {},
    });
    const [categorizedCurrencies, setCategorizedCurrencies] = useState({ orbs: [], essences: [], bones: [] });
    const [availableCurrencies, setAvailableCurrencies] = useState([]);
    const [selectedCurrency, setSelectedCurrency] = useState('');
    const [selectedOmens, setSelectedOmens] = useState([]);
    const [availableOmens, setAvailableOmens] = useState([]);
    const [allOmens, setAllOmens] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [history, setHistory] = useState([]);
    const [itemHistory, setItemHistory] = useState([]);
    const [currencySpent, setCurrencySpent] = useState({});
    const [availableMods, setAvailableMods] = useState({ prefixes: [], suffixes: [] });
    const [modPoolFilter, setModPoolFilter] = useState({ search: '', tags: [], modType: 'all' });
    const [expandedModGroups, setExpandedModGroups] = useState(new Set());
    const [itemBases, setItemBases] = useState({});
    const [selectedSlot, setSelectedSlot] = useState('body_armour');
    const [selectedCategory, setSelectedCategory] = useState('int_armour');
    const [availableBases, setAvailableBases] = useState([]);
    const [selectedBase, setSelectedBase] = useState('');
    const [modsPoolCollapsed, setModsPoolCollapsed] = useState(false);
    const [itemPasteText, setItemPasteText] = useState('');
    const [pasteExpanded, setPasteExpanded] = useState(false);
    const [pasteMessage, setPasteMessage] = useState('');
    const [modsPoolWidth, setModsPoolWidth] = useState(() => {
        const saved = localStorage.getItem('modsPoolWidth');
        return saved ? parseInt(saved) : 600;
    });
    const [isResizing, setIsResizing] = useState(false);
    // Vertical resize state
    const [verticalSizes, setVerticalSizes] = useState(() => {
        const saved = localStorage.getItem('verticalSizes');
        return saved ? JSON.parse(saved) : {
            currencyCompact: 100,
            itemDisplay: 350,
            currencySection: 150,
            historySection: 200
        };
    });
    const [verticalResizing, setVerticalResizing] = useState({
        active: false,
        section: '',
        startY: 0,
        startHeight: 0
    });
    useEffect(() => {
        loadCurrencies();
        loadItemBases();
        loadAllOmens();
    }, []);
    useEffect(() => {
        loadAvailableBases();
    }, [selectedSlot, selectedCategory]);
    useEffect(() => {
        loadAvailableCurrencies();
        loadAvailableMods();
    }, [item]);
    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                e.preventDefault();
                handleUndo();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [itemHistory]);
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isResizing)
                return;
            const newWidth = e.clientX - 32;
            const maxWidth = Math.floor(window.innerWidth * 0.8); // 80% of screen width
            if (newWidth >= 300 && newWidth <= maxWidth) {
                setModsPoolWidth(newWidth);
            }
        };
        const handleMouseUp = () => {
            if (isResizing) {
                setIsResizing(false);
                localStorage.setItem('modsPoolWidth', modsPoolWidth.toString());
            }
        };
        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        }
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing, modsPoolWidth]);
    // Vertical resize handlers
    useEffect(() => {
        const handleVerticalMouseMove = (e) => {
            if (!verticalResizing.active)
                return;
            const deltaY = e.clientY - verticalResizing.startY;
            const newHeight = Math.max(150, verticalResizing.startHeight + deltaY);
            setVerticalSizes((prev) => (Object.assign(Object.assign({}, prev), { [verticalResizing.section]: newHeight })));
        };
        const handleVerticalMouseUp = () => {
            if (verticalResizing.active) {
                setVerticalResizing({
                    active: false,
                    section: '',
                    startY: 0,
                    startHeight: 0
                });
                localStorage.setItem('verticalSizes', JSON.stringify(verticalSizes));
            }
        };
        if (verticalResizing.active) {
            document.addEventListener('mousemove', handleVerticalMouseMove);
            document.addEventListener('mouseup', handleVerticalMouseUp);
            document.body.style.cursor = 'row-resize';
            document.body.style.userSelect = 'none';
        }
        return () => {
            document.removeEventListener('mousemove', handleVerticalMouseMove);
            document.removeEventListener('mouseup', handleVerticalMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [verticalResizing, verticalSizes]);
    const handleVerticalResizeStart = (section, e) => {
        setVerticalResizing({
            active: true,
            section: section,
            startY: e.clientY,
            startHeight: verticalSizes[section]
        });
    };
    const loadCurrencies = () => __awaiter(this, void 0, void 0, function* () {
        try {
            const categorized = yield craftingApi.getCategorizedCurrencies();
            setCategorizedCurrencies(categorized);
            if (categorized.orbs.length > 0) {
                setSelectedCurrency(categorized.orbs[0]);
            }
        }
        catch (err) {
            console.error('Failed to load currencies:', err);
        }
    });
    const loadAvailableCurrencies = () => __awaiter(this, void 0, void 0, function* () {
        try {
            const data = yield craftingApi.getAvailableCurrenciesForItem(item);
            setAvailableCurrencies(data);
        }
        catch (err) {
            console.error('Failed to load available currencies:', err);
        }
    });
    const loadAvailableMods = () => __awaiter(this, void 0, void 0, function* () {
        try {
            const data = yield craftingApi.getAvailableMods(item);
            setAvailableMods({
                prefixes: data.prefixes,
                suffixes: data.suffixes,
            });
        }
        catch (err) {
            console.error('Failed to load available mods:', err);
        }
    });
    const loadItemBases = () => __awaiter(this, void 0, void 0, function* () {
        try {
            const data = yield craftingApi.getItemBases();
            setItemBases(data);
            // Set default selected category (int_armour for body_armour)
            if (data.body_armour && data.body_armour.includes('int_armour')) {
                setSelectedCategory('int_armour');
            }
        }
        catch (err) {
            console.error('Failed to load item bases:', err);
        }
    });
    const loadAvailableBases = () => __awaiter(this, void 0, void 0, function* () {
        try {
            const bases = yield craftingApi.getBasesForSlotCategory(selectedSlot, selectedCategory);
            setAvailableBases(bases);
            // Set default selected base (first one) and create item
            if (bases.length > 0) {
                const firstBase = bases[0];
                setSelectedBase(firstBase.name);
                const baseStats = firstBase.base_stats || {};
                setItem({
                    base_name: firstBase.name,
                    base_category: selectedCategory,
                    rarity: 'Normal',
                    item_level: 65,
                    quality: 20,
                    implicit_mods: [],
                    prefix_mods: [],
                    suffix_mods: [],
                    corrupted: false,
                    base_stats: baseStats,
                    calculated_stats: calculateItemStats(baseStats, 20),
                });
            }
        }
        catch (err) {
            console.error('Failed to load available bases:', err);
        }
    });
    // Helper function to calculate stats with quality
    const calculateItemStats = (baseStats, quality) => {
        const calculated = Object.assign({}, baseStats);
        // Apply quality bonuses to armor, evasion, and energy_shield
        for (const [stat, value] of Object.entries(calculated)) {
            if (['armour', 'evasion', 'energy_shield'].includes(stat)) {
                calculated[stat] = Math.floor(value * (1 + quality / 100));
            }
        }
        return calculated;
    };
    const loadAllOmens = () => __awaiter(this, void 0, void 0, function* () {
        const allOmenNames = [
            "Omen of Whittling",
            "Omen of Greater Exaltation",
            "Omen of Sinistral Exaltation",
            "Omen of Dextral Exaltation",
            "Omen of Sinistral Erasure",
            "Omen of Dextral Erasure",
            "Omen of Greater Annulment",
            "Omen of Sinistral Annulment",
            "Omen of Dextral Annulment",
            "Omen of Sinistral Coronation",
            "Omen of Dextral Coronation",
            "Omen of Sinistral Alchemy",
            "Omen of Dextral Alchemy",
            "Omen of Corruption"
        ];
        setAllOmens(allOmenNames);
    });
    const loadAvailableOmens = (currencyName) => __awaiter(this, void 0, void 0, function* () {
        try {
            const omens = yield craftingApi.getAvailableOmensForCurrency(currencyName);
            setAvailableOmens(omens);
        }
        catch (err) {
            console.error('Failed to load available omens:', err);
            setAvailableOmens([]);
        }
    });
    const toggleOmen = (omen) => {
        setSelectedOmens(prev => prev.includes(omen)
            ? prev.filter(o => o !== omen)
            : [...prev, omen]);
    };
    const handleCraft = (currencyName) => __awaiter(this, void 0, void 0, function* () {
        var _a, _b;
        setLoading(true);
        setMessage('');
        try {
            let result;
            if (selectedOmens.length > 0) {
                result = yield craftingApi.simulateCraftingWithOmens(item, currencyName, selectedOmens);
            }
            else {
                result = yield craftingApi.simulateCrafting({
                    item,
                    currency_name: currencyName,
                });
            }
            if (result.success && result.result_item) {
                setItemHistory([...itemHistory, item]);
                setItem(result.result_item);
                const omenText = selectedOmens.length > 0 ? ` with omens [${selectedOmens.join(', ')}]` : '';
                setMessage(`✓ ${result.message}`);
                setHistory([...history, `Used ${currencyName}${omenText}: ${result.message}`]);
                setCurrencySpent(prev => (Object.assign(Object.assign({}, prev), { [currencyName]: (prev[currencyName] || 0) + 1 })));
                // Clear selected omens after use
                setSelectedOmens([]);
            }
            else {
                setMessage(`✗ ${result.message}`);
            }
        }
        catch (err) {
            setMessage(`Error: ${((_b = (_a = err.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.detail) || 'Failed to simulate'}`);
        }
        finally {
            setLoading(false);
        }
    });
    const handleUndo = () => {
        if (itemHistory.length === 0)
            return;
        const previousItem = itemHistory[itemHistory.length - 1];
        const lastHistory = history[history.length - 1];
        const currencyMatch = lastHistory.match(/Used ([^:]+):/);
        if (currencyMatch) {
            const currencyName = currencyMatch[1];
            setCurrencySpent(prev => {
                const newSpent = Object.assign({}, prev);
                if (newSpent[currencyName] > 1) {
                    newSpent[currencyName]--;
                }
                else {
                    delete newSpent[currencyName];
                }
                return newSpent;
            });
        }
        setItem(previousItem);
        setItemHistory(itemHistory.slice(0, -1));
        setHistory(history.slice(0, -1));
        setMessage('↶ Undone last action');
    };
    const handleReset = () => {
        setItem({
            base_name: selectedBase || getDisplayName(selectedSlot, selectedCategory),
            base_category: selectedCategory,
            rarity: 'Normal',
            item_level: 65,
            quality: 20,
            implicit_mods: [],
            prefix_mods: [],
            suffix_mods: [],
            corrupted: false,
            base_stats: {},
            calculated_stats: {},
        });
        setMessage('');
        setHistory([]);
        setItemHistory([]);
        setCurrencySpent({});
    };
    const getRarityColor = (rarity) => {
        switch (rarity) {
            case 'Normal': return '#c8c8c8';
            case 'Magic': return '#8888ff';
            case 'Rare': return '#ffff77';
            case 'Unique': return '#af6025';
            default: return '#c8c8c8';
        }
    };
    const renderModifier = (mod) => {
        const value = mod.current_value !== undefined
            ? Math.round(mod.current_value)
            : mod.stat_min !== undefined && mod.stat_max !== undefined
                ? `${mod.stat_min}-${mod.stat_max}`
                : '?';
        const statText = mod.stat_text.replace('{}', value.toString());
        const modName = mod.name || 'Unknown';
        const rangeText = mod.stat_min !== undefined && mod.stat_max !== undefined
            ? `(${mod.stat_min}-${mod.stat_max})`
            : '';
        const tooltipText = [
            `Name: ${modName}`,
            `Tier: ${mod.tier}`,
            mod.required_ilvl ? `Required ilvl: ${mod.required_ilvl}` : null,
            mod.mod_group ? `Group: ${mod.mod_group}` : null,
            mod.stat_min !== undefined && mod.stat_max !== undefined
                ? `Range: ${mod.stat_min}-${mod.stat_max}`
                : null,
            mod.tags && mod.tags.length > 0 ? `Tags: ${mod.tags.join(', ')}` : null,
        ].filter(Boolean).join('\n');
        return (_jsxs("span", { className: "mod-with-info", title: tooltipText, children: [statText, " ", rangeText && _jsx("span", { className: "mod-range", children: rangeText })] }));
    };
    const getGroupedMods = (modType) => {
        let mods = modType === 'prefix' ? availableMods.prefixes : availableMods.suffixes;
        if (modPoolFilter.search) {
            const search = modPoolFilter.search.toLowerCase();
            mods = mods.filter(mod => {
                var _a;
                return mod.name.toLowerCase().includes(search) ||
                    mod.stat_text.toLowerCase().includes(search) ||
                    ((_a = mod.mod_group) === null || _a === void 0 ? void 0 : _a.toLowerCase().includes(search));
            });
        }
        if (modPoolFilter.tags.length > 0) {
            mods = mods.filter(mod => modPoolFilter.tags.some(tag => { var _a; return (_a = mod.tags) === null || _a === void 0 ? void 0 : _a.includes(tag); }));
        }
        // Group by mod_group and sort by tier (tier 1 is highest)
        const grouped = mods.reduce((acc, mod) => {
            const group = mod.mod_group || 'unknown';
            if (!acc[group])
                acc[group] = [];
            acc[group].push(mod);
            return acc;
        }, {});
        // Sort each group by tier (ascending - tier 1 first)
        Object.keys(grouped).forEach(group => {
            grouped[group].sort((a, b) => a.tier - b.tier);
        });
        return grouped;
    };
    const toggleModGroup = (groupKey) => {
        const newExpanded = new Set(expandedModGroups);
        if (newExpanded.has(groupKey)) {
            newExpanded.delete(groupKey);
        }
        else {
            newExpanded.add(groupKey);
        }
        setExpandedModGroups(newExpanded);
    };
    const getDisplayName = (slot, category) => {
        return `${category.replace('_', ' ')} ${slot.replace('_', ' ')}`;
    };
    const formatSlotName = (slot) => {
        return slot.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };
    const formatCategoryName = (category) => {
        return category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };
    const formatStatName = (statName) => {
        const statNames = {
            'armour': 'Armour',
            'evasion': 'Evasion Rating',
            'energy_shield': 'Energy Shield',
        };
        return statNames[statName] || statName;
    };
    // Currency icon helpers
    const getCurrencyIconUrl = (currency) => {
        const iconMap = {
            "Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
            "Greater Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
            "Perfect Orb of Transmutation": "https://www.poe2wiki.net/images/6/67/Orb_of_Transmutation_inventory_icon.png",
            "Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
            "Greater Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
            "Perfect Orb of Augmentation": "https://www.poe2wiki.net/images/c/cb/Orb_of_Augmentation_inventory_icon.png",
            "Orb of Alchemy": "https://www.poe2wiki.net/images/9/9f/Orb_of_Alchemy_inventory_icon.png",
            "Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
            "Greater Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
            "Perfect Regal Orb": "https://www.poe2wiki.net/images/3/33/Regal_Orb_inventory_icon.png",
            "Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
            "Greater Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
            "Perfect Exalted Orb": "https://www.poe2wiki.net/images/2/26/Exalted_Orb_inventory_icon.png",
            "Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
            "Greater Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
            "Perfect Chaos Orb": "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png",
            "Divine Orb": "https://www.poe2wiki.net/images/5/58/Divine_Orb_inventory_icon.png"
        };
        // Handle Essences - based on poe2wiki.net/wiki/Essence
        if (currency.includes('Essence of')) {
            // Map our backend names to actual PoE2 wiki icon URLs
            // Note: PoE2 uses different names (Flames not Fire, Ice not Cold, etc.)
            const essenceIconMap = {
                'Fire': 'https://www.poe2wiki.net/images/d/d4/Essence_of_Flames_inventory_icon.png',
                'Cold': 'https://www.poe2wiki.net/images/d/df/Essence_of_Ice_inventory_icon.png',
                'Lightning': 'https://www.poe2wiki.net/images/c/ca/Essence_of_Electricity_inventory_icon.png',
                'Life': 'https://www.poe2wiki.net/images/b/b2/Essence_of_the_Body_inventory_icon.png',
                'Mana': 'https://www.poe2wiki.net/images/6/62/Essence_of_the_Mind_inventory_icon.png',
                'Armor': 'https://www.poe2wiki.net/images/f/fc/Essence_of_the_Protector_inventory_icon.png',
                'Evasion': 'https://www.poe2wiki.net/images/d/dc/Essence_of_Haste_inventory_icon.png',
                'Energy Shield': 'https://www.poe2wiki.net/images/d/d1/Essence_of_Warding_inventory_icon.png',
                'Delirium': 'https://www.poe2wiki.net/images/9/9b/Essence_of_Delirium_inventory_icon.png',
                'Horror': 'https://www.poe2wiki.net/images/0/06/Essence_of_Horror_inventory_icon.png',
                'Hysteria': 'https://www.poe2wiki.net/images/b/b7/Essence_of_Hysteria_inventory_icon.png',
                'Insanity': 'https://www.poe2wiki.net/images/d/d0/Essence_of_Insanity_inventory_icon.png',
            };
            // Check which essence this is (works for Greater/Perfect variants too)
            for (const [key, url] of Object.entries(essenceIconMap)) {
                if (currency.includes(key)) {
                    return url;
                }
            }
        }
        // Handle Abyssal Bones
        if (currency.startsWith('Abyssal') || currency.startsWith('Ancient Abyssal')) {
            // Generic bone icon for now - can be customized per bone type
            return "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
        }
        return iconMap[currency] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
    };
    const getOmenIconUrl = (omen) => {
        // Based on poe2wiki.net/wiki/Category:Omen_icons - Correct URLs verified from wiki
        const omenIconMap = {
            "Omen of Whittling": "https://www.poe2wiki.net/images/8/81/Omen_of_Whittling_inventory_icon.png",
            "Omen of Greater Exaltation": "https://www.poe2wiki.net/images/6/6b/Omen_of_Greater_Exaltation_inventory_icon.png",
            "Omen of Sinistral Exaltation": "https://www.poe2wiki.net/images/0/06/Omen_of_Sinistral_Exaltation_inventory_icon.png",
            "Omen of Dextral Exaltation": "https://www.poe2wiki.net/images/4/4d/Omen_of_Dextral_Exaltation_inventory_icon.png",
            "Omen of Sinistral Erasure": "https://www.poe2wiki.net/images/4/47/Omen_of_Sinistral_Erasure_inventory_icon.png",
            "Omen of Dextral Erasure": "https://www.poe2wiki.net/images/0/0b/Omen_of_Dextral_Erasure_inventory_icon.png",
            "Omen of Greater Annulment": "https://www.poe2wiki.net/images/d/df/Omen_of_Greater_Annulment_inventory_icon.png",
            "Omen of Sinistral Annulment": "https://www.poe2wiki.net/images/4/45/Omen_of_Sinistral_Annulment_inventory_icon.png",
            "Omen of Dextral Annulment": "https://www.poe2wiki.net/images/e/ef/Omen_of_Dextral_Annulment_inventory_icon.png",
            "Omen of Sinistral Coronation": "https://www.poe2wiki.net/images/6/66/Omen_of_Sinistral_Coronation_inventory_icon.png",
            "Omen of Dextral Coronation": "https://www.poe2wiki.net/images/1/1c/Omen_of_Dextral_Coronation_inventory_icon.png",
            "Omen of Sinistral Alchemy": "https://www.poe2wiki.net/images/b/b6/Omen_of_Sinistral_Alchemy_inventory_icon.png",
            "Omen of Dextral Alchemy": "https://www.poe2wiki.net/images/2/2c/Omen_of_Dextral_Alchemy_inventory_icon.png",
            "Omen of Corruption": "https://www.poe2wiki.net/images/a/a2/Omen_of_Corruption_inventory_icon.png"
        };
        return omenIconMap[omen] || "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
    };
    const handlePasteItem = () => __awaiter(this, void 0, void 0, function* () {
        var _a, _b;
        if (!itemPasteText.trim()) {
            setPasteMessage('Please paste item text');
            return;
        }
        setLoading(true);
        setPasteMessage('');
        try {
            const result = yield craftingApi.parseItem(itemPasteText);
            if (result.success && result.item) {
                setItem(result.item);
                setSelectedSlot(result.parsed_info.base_type.includes('Body Armour') || result.parsed_info.base_type.includes('Robe') || result.parsed_info.base_type.includes('Vest') || result.parsed_info.base_type.includes('Plate') ? 'body_armour' : 'body_armour');
                setSelectedCategory(result.item.base_category);
                setPasteMessage(`✓ Loaded ${result.parsed_info.rarity} ${result.parsed_info.base_type}`);
                setHistory([]);
                setItemHistory([]);
                setCurrencySpent({});
                setPasteExpanded(false);
                setItemPasteText('');
            }
        }
        catch (err) {
            setPasteMessage(`✗ Error: ${((_b = (_a = err.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.detail) || 'Failed to parse item'}`);
        }
        finally {
            setLoading(false);
        }
    });
    return (_jsxs("div", { className: "crafting-simulator", children: [_jsx("h2", { className: "page-title", children: "Crafting Simulator" }), _jsx("p", { className: "page-subtitle", children: "Experiment with crafting currencies on items" }), _jsxs("div", { className: "item-paste-section", children: [_jsx("div", { className: "paste-header", onClick: () => setPasteExpanded(!pasteExpanded), children: _jsxs("h3", { children: ["Paste Item from Game ", pasteExpanded ? '▼' : '▶'] }) }), pasteExpanded && (_jsxs("div", { className: "paste-content", children: [_jsx("p", { className: "paste-instructions", children: "Copy an item from PoE2 (Ctrl+C in-game) and paste it here. Both simple and detailed formats are supported." }), _jsx("textarea", { className: "item-paste-textarea", value: itemPasteText, onChange: (e) => setItemPasteText(e.target.value), placeholder: "Item Class: Body Armours\nRarity: Rare\nViper Coat\nVile Robe\n--------\nQuality: +20% (augmented)\n...", rows: 12 }), _jsxs("div", { className: "paste-actions", children: [_jsx("button", { className: "paste-button", onClick: handlePasteItem, disabled: loading || !itemPasteText.trim(), children: "Load Item" }), _jsx("button", { className: "clear-button", onClick: () => { setItemPasteText(''); setPasteMessage(''); }, disabled: !itemPasteText, children: "Clear" })] }), pasteMessage && (_jsx("div", { className: `paste-message ${pasteMessage.startsWith('✓') ? 'success' : 'error'}`, children: pasteMessage }))] }))] }), _jsxs("div", { className: "item-base-selector", children: [_jsx("h3", { children: "Item Base Selection" }), _jsxs("div", { className: "base-selector-row", children: [_jsxs("div", { className: "slot-selector", children: [_jsx("label", { htmlFor: "slot-select", children: "Slot:" }), _jsx("select", { id: "slot-select", value: selectedSlot, onChange: (e) => {
                                            setSelectedSlot(e.target.value);
                                            const categoriesForSlot = itemBases[e.target.value];
                                            if (categoriesForSlot && categoriesForSlot.length > 0) {
                                                setSelectedCategory(categoriesForSlot[0]);
                                            }
                                            // Reset bases when slot changes
                                            setAvailableBases([]);
                                            setSelectedBase('');
                                        }, children: Object.keys(itemBases).map(slot => (_jsx("option", { value: slot, children: formatSlotName(slot) }, slot))) })] }), _jsxs("div", { className: "base-selector", children: [_jsx("label", { htmlFor: "category-select", children: "Category:" }), _jsx("select", { id: "category-select", value: selectedCategory, onChange: (e) => {
                                            setSelectedCategory(e.target.value);
                                            // Don't update the item here, wait for base selection
                                            setMessage('');
                                            setHistory([]);
                                            setItemHistory([]);
                                            setCurrencySpent({});
                                        }, children: (itemBases[selectedSlot] || []).map(category => (_jsx("option", { value: category, children: formatCategoryName(category) }, category))) })] }), _jsxs("div", { className: "base-selector", children: [_jsx("label", { htmlFor: "base-select", children: "Base:" }), _jsx("select", { id: "base-select", value: selectedBase, onChange: (e) => {
                                            const selectedBaseName = e.target.value;
                                            const selectedBaseData = availableBases.find(base => base.name === selectedBaseName);
                                            const baseStats = (selectedBaseData === null || selectedBaseData === void 0 ? void 0 : selectedBaseData.base_stats) || {};
                                            setSelectedBase(selectedBaseName);
                                            setItem({
                                                base_name: selectedBaseName,
                                                base_category: selectedCategory,
                                                rarity: 'Normal',
                                                item_level: 65,
                                                quality: 20,
                                                implicit_mods: [],
                                                prefix_mods: [],
                                                suffix_mods: [],
                                                corrupted: false,
                                                base_stats: baseStats,
                                                calculated_stats: calculateItemStats(baseStats, 20),
                                            });
                                            setMessage('');
                                            setHistory([]);
                                            setItemHistory([]);
                                            setCurrencySpent({});
                                        }, disabled: availableBases.length === 0, children: availableBases.map((base, index) => {
                                            const statsText = Object.entries(base.base_stats || {})
                                                .map(([stat, value]) => `${value} ${formatStatName(stat)}`)
                                                .join(', ');
                                            return (_jsxs("option", { value: base.name, title: `${base.description}${statsText ? ` - ${statsText}` : ''}`, children: [base.name, statsText ? ` (${statsText})` : ''] }, `${base.name}-${index}-${JSON.stringify(base.base_stats)}`));
                                        }) })] }), _jsxs("div", { className: "ilvl-selector", children: [_jsx("label", { htmlFor: "ilvl-input", children: "Item Level:" }), _jsx("input", { id: "ilvl-input", type: "number", min: "1", max: "100", value: item.item_level, onChange: (e) => {
                                            const newIlvl = parseInt(e.target.value) || 1;
                                            setItem(Object.assign(Object.assign({}, item), { item_level: Math.max(1, Math.min(100, newIlvl)) }));
                                        } })] }), _jsxs("div", { className: "base-info", children: [_jsx("span", { className: "base-category", children: selectedCategory }), _jsxs("span", { className: "base-ilvl", children: ["ilvl ", item.item_level] }), _jsx("span", { className: "base-slot", children: formatSlotName(selectedSlot) })] })] })] }), _jsxs("div", { className: `simulator-layout ${modsPoolCollapsed ? 'mods-collapsed' : ''}`, children: [_jsxs("div", { className: "mods-pool-panel", style: { width: modsPoolCollapsed ? '60px' : `${modsPoolWidth}px` }, children: [_jsxs("div", { className: "mods-pool-header", children: [_jsxs("div", { className: "mods-pool-title-row", children: [_jsx("h3", { children: "Available Mods" }), _jsx("button", { className: "collapse-button", onClick: () => setModsPoolCollapsed(!modsPoolCollapsed), title: modsPoolCollapsed ? "Expand" : "Collapse", children: modsPoolCollapsed ? '→' : '←' })] }), !modsPoolCollapsed && (_jsxs("div", { className: "mods-pool-stats", children: [_jsxs("span", { className: "stat-badge prefix-badge", children: [availableMods.prefixes.length, " Prefixes"] }), _jsxs("span", { className: "stat-badge suffix-badge", children: [availableMods.suffixes.length, " Suffixes"] })] }))] }), !modsPoolCollapsed && (_jsxs(_Fragment, { children: [_jsx("div", { className: "mods-pool-filters", children: _jsx("input", { type: "text", className: "search-input", placeholder: "Search mods...", value: modPoolFilter.search, onChange: e => setModPoolFilter(Object.assign(Object.assign({}, modPoolFilter), { search: e.target.value })) }) }), _jsxs("div", { className: "mods-pool-columns", children: [_jsxs("div", { className: "mods-pool-column", children: [_jsxs("h4", { className: "column-title", children: ["Prefixes (", Object.keys(getGroupedMods('prefix')).length, " groups)"] }), _jsx("div", { className: "mods-pool-list", children: Object.entries(getGroupedMods('prefix')).map(([groupKey, groupMods]) => {
                                                            const bestTier = groupMods[0]; // Tier 1 (highest)
                                                            const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1));
                                                            const isExpanded = expandedModGroups.has(`prefix-${groupKey}`);
                                                            const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length;
                                                            const allUnavailable = unavailableCount === groupMods.length;
                                                            // Calculate available tier range
                                                            const availableMods = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level);
                                                            const bestAvailableTier = availableMods.length > 0 ? Math.min(...availableMods.map(m => m.tier)) : null;
                                                            const worstTier = Math.max(...groupMods.map(m => m.tier));
                                                            const tierRangeText = bestAvailableTier ? `T${bestAvailableTier}-T${worstTier}` : `T1-T${worstTier}`;
                                                            return (_jsxs("div", { className: "pool-mod-group", children: [_jsxs("div", { className: `pool-mod-group-header prefix ${allUnavailable ? 'all-unavailable' : ''}`, onClick: () => toggleModGroup(`prefix-${groupKey}`), children: [_jsxs("div", { className: "group-main-info", children: [_jsx("span", { className: "pool-mod-stat-main", children: bestTier.stat_text }), _jsxs("div", { className: "group-summary", children: [_jsx("span", { className: `group-tier-range ${allUnavailable ? 'all-unavailable' : ''}`, children: tierRangeText }), _jsxs("span", { className: "group-max-ilvl", children: ["ilvl ", maxIlvl] }), unavailableCount > 0 && (_jsxs("span", { className: `unavailable-badge ${allUnavailable ? 'all-unavailable' : ''}`, children: [unavailableCount, " unavailable"] }))] })] }), _jsx("span", { className: "expand-indicator", children: isExpanded ? '−' : '+' })] }), isExpanded && (_jsx("div", { className: "tier-breakdown", children: groupMods.map((mod, idx) => {
                                                                            const isUnavailable = mod.required_ilvl && mod.required_ilvl > item.item_level;
                                                                            return (_jsxs("div", { className: `tier-item ${isUnavailable ? 'unavailable' : ''}`, children: [_jsxs("div", { className: "tier-header", children: [_jsxs("span", { className: "tier-label", children: ["T", mod.tier] }), _jsxs("span", { className: `tier-ilvl ${isUnavailable ? 'ilvl-too-high' : ''}`, children: ["ilvl ", mod.required_ilvl, isUnavailable && ' ⚠'] })] }), mod.stat_min !== undefined && mod.stat_max !== undefined && (_jsxs("div", { className: "tier-range", children: [mod.stat_min, "-", mod.stat_max] })), mod.tags && mod.tags.length > 0 && (_jsx("div", { className: "tier-tags", children: mod.tags.slice(0, 3).map((tag, i) => (_jsx("span", { className: "pool-tag", children: tag }, i))) }))] }, idx));
                                                                        }) }))] }, groupKey));
                                                        }) })] }), _jsxs("div", { className: "mods-pool-column", children: [_jsxs("h4", { className: "column-title", children: ["Suffixes (", Object.keys(getGroupedMods('suffix')).length, " groups)"] }), _jsx("div", { className: "mods-pool-list", children: Object.entries(getGroupedMods('suffix')).map(([groupKey, groupMods]) => {
                                                            const bestTier = groupMods[0]; // Tier 1 (highest)
                                                            const maxIlvl = Math.max(...groupMods.map(m => m.required_ilvl || 1));
                                                            const isExpanded = expandedModGroups.has(`suffix-${groupKey}`);
                                                            const unavailableCount = groupMods.filter(m => m.required_ilvl && m.required_ilvl > item.item_level).length;
                                                            const allUnavailable = unavailableCount === groupMods.length;
                                                            // Calculate available tier range
                                                            const availableMods = groupMods.filter(m => !m.required_ilvl || m.required_ilvl <= item.item_level);
                                                            const bestAvailableTier = availableMods.length > 0 ? Math.min(...availableMods.map(m => m.tier)) : null;
                                                            const worstTier = Math.max(...groupMods.map(m => m.tier));
                                                            const tierRangeText = bestAvailableTier ? `T${bestAvailableTier}-T${worstTier}` : `T1-T${worstTier}`;
                                                            return (_jsxs("div", { className: "pool-mod-group", children: [_jsxs("div", { className: `pool-mod-group-header suffix ${allUnavailable ? 'all-unavailable' : ''}`, onClick: () => toggleModGroup(`suffix-${groupKey}`), children: [_jsxs("div", { className: "group-main-info", children: [_jsx("span", { className: "pool-mod-stat-main", children: bestTier.stat_text }), _jsxs("div", { className: "group-summary", children: [_jsx("span", { className: `group-tier-range ${allUnavailable ? 'all-unavailable' : ''}`, children: tierRangeText }), _jsxs("span", { className: "group-max-ilvl", children: ["ilvl ", maxIlvl] }), unavailableCount > 0 && (_jsxs("span", { className: `unavailable-badge ${allUnavailable ? 'all-unavailable' : ''}`, children: [unavailableCount, " unavailable"] }))] })] }), _jsx("span", { className: "expand-indicator", children: isExpanded ? '−' : '+' })] }), isExpanded && (_jsx("div", { className: "tier-breakdown", children: groupMods.map((mod, idx) => {
                                                                            const isUnavailable = mod.required_ilvl && mod.required_ilvl > item.item_level;
                                                                            return (_jsxs("div", { className: `tier-item ${isUnavailable ? 'unavailable' : ''}`, children: [_jsxs("div", { className: "tier-header", children: [_jsxs("span", { className: "tier-label", children: ["T", mod.tier] }), _jsxs("span", { className: `tier-ilvl ${isUnavailable ? 'ilvl-too-high' : ''}`, children: ["ilvl ", mod.required_ilvl, isUnavailable && ' ⚠'] })] }), mod.stat_min !== undefined && mod.stat_max !== undefined && (_jsxs("div", { className: "tier-range", children: [mod.stat_min, "-", mod.stat_max] })), mod.tags && mod.tags.length > 0 && (_jsx("div", { className: "tier-tags", children: mod.tags.slice(0, 3).map((tag, i) => (_jsx("span", { className: "pool-tag", children: tag }, i))) }))] }, idx));
                                                                        }) }))] }, groupKey));
                                                        }) })] })] })] }))] }), !modsPoolCollapsed && (_jsx("div", { className: "resize-handle", onMouseDown: () => setIsResizing(true), children: _jsx("div", { className: "resize-line" }) })), _jsx("div", { className: "center-panel", children: _jsx("div", { className: "currency-section-compact", style: { height: `${verticalSizes.currencyCompact}px`, overflow: 'auto' }, children: _jsxs("div", { className: "currency-five-tables", children: [_jsxs("div", { className: "currency-table", children: [_jsx("h5", { className: "currency-table-title", children: "Orbs" }), _jsxs("div", { className: "currency-horizontal-rows", children: [_jsx("div", { className: "currency-family-row", children: ['Orb of Transmutation', 'Greater Orb of Transmutation', 'Perfect Orb of Transmutation'].map((currency) => {
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) }), _jsx("div", { className: "currency-family-row", children: ['Orb of Augmentation', 'Greater Orb of Augmentation', 'Perfect Orb of Augmentation'].map((currency) => {
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) }), _jsx("div", { className: "currency-family-row", children: ['Regal Orb', 'Greater Regal Orb', 'Perfect Regal Orb'].map((currency) => {
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) }), _jsx("div", { className: "currency-family-row", children: ['Exalted Orb', 'Greater Exalted Orb', 'Perfect Exalted Orb'].map((currency) => {
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) }), _jsx("div", { className: "currency-family-row", children: ['Chaos Orb', '', ''].map((currency, index) => {
                                                            if (!currency) {
                                                                return _jsx("div", { className: "currency-empty-slot" }, index);
                                                            }
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) })] })] }), _jsxs("div", { className: "currency-table", children: [_jsx("h5", { className: "currency-table-title", children: "Special" }), _jsxs("div", { className: "currency-horizontal-rows", children: [_jsx("div", { className: "currency-family-row", children: ['Orb of Alchemy', 'Vaal Orb', 'Orb of Annulment'].map((currency) => {
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) }), _jsx("div", { className: "currency-family-row", children: ['Orb of Fracturing', 'Divine Orb', ''].map((currency, index) => {
                                                            if (!currency) {
                                                                return _jsx("div", { className: "currency-empty-slot" }, index);
                                                            }
                                                            const isAvailable = availableCurrencies.includes(currency);
                                                            const isSelected = selectedCurrency === currency;
                                                            return (_jsx("div", { className: `currency-icon-button ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                                    if (isAvailable) {
                                                                        setSelectedCurrency(currency);
                                                                        loadAvailableOmens(currency);
                                                                    }
                                                                }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img", onError: (e) => {
                                                                        e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                    } }) }, currency));
                                                        }) })] })] }), _jsxs("div", { className: "currency-table", children: [_jsx("h5", { className: "currency-table-title", children: "Bones" }), _jsx("div", { className: "currency-icon-grid-compact", children: categorizedCurrencies.bones.map((currency) => {
                                                    const isAvailable = availableCurrencies.includes(currency);
                                                    const isSelected = selectedCurrency === currency;
                                                    return (_jsx("div", { className: `currency-icon-button-small ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                            if (isAvailable) {
                                                                setSelectedCurrency(currency);
                                                                loadAvailableOmens(currency);
                                                            }
                                                        }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img-small", onError: (e) => {
                                                                e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                            } }) }, currency));
                                                }) })] }), _jsxs("div", { className: "currency-table", children: [_jsx("h5", { className: "currency-table-title", children: "Essences" }), _jsx("div", { className: "currency-icon-grid-compact", children: categorizedCurrencies.essences.map((currency) => {
                                                    const isAvailable = availableCurrencies.includes(currency);
                                                    const isSelected = selectedCurrency === currency;
                                                    return (_jsx("div", { className: `currency-icon-button-small ${!isAvailable ? 'currency-disabled' : ''} ${isSelected ? 'currency-selected' : ''}`, onClick: () => {
                                                            if (isAvailable) {
                                                                setSelectedCurrency(currency);
                                                                loadAvailableOmens(currency);
                                                            }
                                                        }, onDoubleClick: () => isAvailable && handleCraft(currency), title: `${currency}\n${getCurrencyDescription(currency)}\n\nDouble-click to apply`, children: _jsx("img", { src: getCurrencyIconUrl(currency), alt: currency, className: "currency-icon-img-small", onError: (e) => {
                                                                e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                            } }) }, currency));
                                                }) })] }), _jsxs("div", { className: "currency-table omen-table", children: [_jsx("h5", { className: "currency-table-title", children: "Omens" }), _jsx("div", { className: "currency-icon-grid-compact", children: allOmens.map(omen => {
                                                    const isCompatible = availableOmens.includes(omen);
                                                    const isActive = selectedOmens.includes(omen);
                                                    const canActivate = !selectedCurrency || isCompatible;
                                                    return (_jsxs("div", { className: `currency-icon-button-small ${isActive ? 'omen-active' : ''} ${!canActivate ? 'omen-incompatible' : ''}`, onClick: () => {
                                                            if (canActivate) {
                                                                toggleOmen(omen);
                                                            }
                                                        }, title: `${omen}\n${getOmenDescription(omen)}\n\nClick to ${isActive ? 'deactivate' : 'activate'}`, children: [_jsx("img", { src: getOmenIconUrl(omen), alt: omen, className: "currency-icon-img-small", onError: (e) => {
                                                                    e.target.src = "https://www.poe2wiki.net/images/9/9c/Chaos_Orb_inventory_icon.png";
                                                                } }), isActive && (_jsx("div", { className: "omen-active-indicator", children: "\u2713" }))] }, omen));
                                                }) }), selectedOmens.length > 0 && (_jsxs("div", { className: "selected-omens-info", children: [_jsx("strong", { children: "Active:" }), " ", selectedOmens.map(o => o.replace('Omen of ', '')).join(', ')] }))] })] }) }) }), message && (_jsx("div", { className: `message-inline ${message.startsWith('✓') ? 'success' : message.startsWith('↶') ? 'info' : 'error'}`, children: message }))] }), _jsx("div", { className: "resize-handle-vertical", onMouseDown: (e) => handleVerticalResizeStart('currencyCompact', e), children: _jsx("div", { className: "resize-line-vertical" }) }), _jsxs("div", { className: "item-display", style: { height: `${verticalSizes.itemDisplay}px`, overflow: 'auto' }, children: [_jsxs("div", { className: "item-header", children: [_jsx("h3", { className: "item-name", style: { color: getRarityColor(item.rarity) }, children: item.base_name }), _jsx("span", { className: "item-rarity-badge", children: item.rarity })] }), _jsxs("div", { className: "item-details", children: [_jsxs("div", { className: "detail-row", children: [_jsx("span", { className: "detail-label", children: "Item Level:" }), _jsx("span", { className: "detail-value", children: item.item_level })] }), _jsxs("div", { className: "detail-row", children: [_jsx("span", { className: "detail-label", children: "Quality:" }), _jsxs("span", { className: "detail-value", children: ["+", item.quality, "%"] })] }), _jsxs("div", { className: "detail-row", children: [_jsx("span", { className: "detail-label", children: "Affixes:" }), _jsxs("span", { className: "detail-value", children: [item.prefix_mods.length + item.suffix_mods.length, " / 6"] })] }), Object.keys(item.calculated_stats || {}).length > 0 && (_jsxs("div", { className: "stats-section", children: [_jsx("h4", { className: "stats-title", children: "Defence" }), Object.entries(item.calculated_stats).map(([statName, value]) => (_jsxs("div", { className: "stat-row", children: [_jsxs("span", { className: "stat-label", children: [formatStatName(statName), ":"] }), _jsx("span", { className: "stat-value", children: value })] }, statName)))] }))] }), item.implicit_mods.length > 0 && (_jsxs("div", { className: "mods-section", children: [_jsx("h4", { className: "mods-title", children: "Implicit" }), item.implicit_mods.map((mod, idx) => (_jsx("div", { className: "mod-line implicit", children: renderModifier(mod) }, idx)))] })), item.prefix_mods.length > 0 && (_jsxs("div", { className: "mods-section", children: [_jsxs("h4", { className: "mods-title", children: ["Prefixes (", item.prefix_mods.length, "/3)"] }), item.prefix_mods.map((mod, idx) => (_jsxs("div", { className: "mod-line prefix", children: [_jsx("div", { className: "mod-stat", children: renderModifier(mod) }), _jsxs("div", { className: "mod-metadata", children: [_jsxs("span", { className: "mod-tier", children: ["T", mod.tier] }), _jsx("span", { className: "mod-name", children: mod.name }), mod.tags && mod.tags.length > 0 && (_jsx("div", { className: "mod-tags", children: mod.tags.slice(0, 2).map((tag, i) => (_jsx("span", { className: "mod-tag", children: tag }, i))) }))] })] }, idx)))] })), item.suffix_mods.length > 0 && (_jsxs("div", { className: "mods-section", children: [_jsxs("h4", { className: "mods-title", children: ["Suffixes (", item.suffix_mods.length, "/3)"] }), item.suffix_mods.map((mod, idx) => (_jsxs("div", { className: "mod-line suffix", children: [_jsx("div", { className: "mod-stat", children: renderModifier(mod) }), _jsxs("div", { className: "mod-metadata", children: [_jsxs("span", { className: "mod-tier", children: ["T", mod.tier] }), _jsx("span", { className: "mod-name", children: mod.name }), mod.tags && mod.tags.length > 0 && (_jsx("div", { className: "mod-tags", children: mod.tags.slice(0, 2).map((tag, i) => (_jsx("span", { className: "mod-tag", children: tag }, i))) }))] })] }, idx)))] })), item.prefix_mods.length === 0 && item.suffix_mods.length === 0 && (_jsx("div", { className: "empty-mods", children: _jsx("p", { children: "No explicit modifiers yet" }) })), item.corrupted && (_jsx("div", { className: "corrupted-tag", children: "Corrupted" }))] }), _jsx("div", { className: "resize-handle-vertical", onMouseDown: (e) => handleVerticalResizeStart('itemDisplay', e), children: _jsx("div", { className: "resize-line-vertical" }) }), _jsx("button", { className: "reset-button", onClick: handleReset, children: "Reset Item" }), Object.keys(currencySpent).length > 0 && (_jsxs(_Fragment, { children: [_jsxs("div", { className: "currency-tracker", style: { height: `${verticalSizes.currencySection}px`, overflow: 'auto' }, children: [_jsx("h3", { children: "Currency Spent" }), _jsx("div", { className: "currency-spent-list", children: Object.entries(currencySpent).map(([currency, count]) => (_jsxs("div", { className: "currency-spent-item", children: [_jsx("span", { className: "currency-spent-name", children: currency }), _jsxs("span", { className: "currency-spent-count", children: ["\u00D7", count] })] }, currency))) })] }), _jsx("div", { className: "resize-handle-vertical", onMouseDown: (e) => handleVerticalResizeStart('currencySection', e), children: _jsx("div", { className: "resize-line-vertical" }) })] })), _jsx("div", { className: "resize-handle-vertical", onMouseDown: (e) => handleVerticalResizeStart('historySection', e), children: _jsx("div", { className: "resize-line-vertical" }) }), _jsxs("div", { className: "history-section", style: { height: `${verticalSizes.historySection}px`, overflow: 'auto' }, children: [_jsx("h3", { children: "Crafting History" }), history.length === 0 ? (_jsx("p", { className: "empty-history", children: "No actions yet" })) : (_jsx("div", { className: "history-list", children: history.map((entry, idx) => (_jsxs("div", { className: "history-entry", children: [_jsxs("span", { className: "history-number", children: [idx + 1, "."] }), _jsx("span", { className: "history-text", children: entry })] }, idx))) }))] })] }));
    div >
    ;
    div >
    ;
}
export default CraftingSimulator;
