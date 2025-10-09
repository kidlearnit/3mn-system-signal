#!/bin/bash

# Script để drop tables và xóa data
# Dùng khi data bị sai hoặc cần reset

echo "🗑️  Database Data Cleanup Tool"
echo "=============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to show current status
show_status() {
    echo -e "${BLUE}📊 Current Database Status:${NC}"
    echo "=========================="
    
    # Check if containers are running
    if ! docker-compose ps | grep -q "running"; then
        echo -e "${RED}❌ Containers are not running${NC}"
        echo -e "${YELLOW}💡 Run ./start.sh first${NC}"
        exit 1
    fi
    
    # Show table counts
    echo "Table records:"
    docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
        SELECT 
            table_name as 'Table',
            table_rows as 'Records'
        FROM information_schema.tables 
        WHERE table_schema = 'trading'
        AND table_type = 'BASE TABLE'
        ORDER BY table_rows DESC;
    " 2>/dev/null || echo "❌ Cannot connect to database"
}

# Function to clear data only
clear_data() {
    echo -e "${YELLOW}🧹 Clearing data only (keeping table structure)...${NC}"
    
    docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
        DELETE FROM signals;
        DELETE FROM signal_aggregation;
        DELETE FROM signal_history;
        DELETE FROM indicators_macd;
        DELETE FROM candles_tf;
        DELETE FROM candles_1m;
        ALTER TABLE signals AUTO_INCREMENT = 1;
        ALTER TABLE signal_aggregation AUTO_INCREMENT = 1;
        ALTER TABLE signal_history AUTO_INCREMENT = 1;
        ALTER TABLE indicators_macd AUTO_INCREMENT = 1;
        ALTER TABLE candles_tf AUTO_INCREMENT = 1;
        ALTER TABLE candles_1m AUTO_INCREMENT = 1;
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Data cleared successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to clear data${NC}"
    fi
}

# Function to drop data tables
drop_data_tables() {
    echo -e "${YELLOW}🗑️  Dropping data tables...${NC}"
    
    docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
        DROP TABLE IF EXISTS signals;
        DROP TABLE IF EXISTS signal_aggregation;
        DROP TABLE IF EXISTS signal_history;
        DROP TABLE IF EXISTS indicators_macd;
        DROP TABLE IF EXISTS candles_tf;
        DROP TABLE IF EXISTS candles_1m;
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Data tables dropped successfully!${NC}"
        echo -e "${BLUE}💡 Run ./start.sh to recreate tables${NC}"
    else
        echo -e "${RED}❌ Failed to drop data tables${NC}"
    fi
}

# Function to drop all tables
drop_all_tables() {
    echo -e "${RED}⚠️  WARNING: This will DELETE ALL TABLES!${NC}"
    echo -e "${RED}⚠️  This action cannot be undone!${NC}"
    echo ""
    
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [[ $confirm == "yes" || $confirm == "y" ]]; then
        echo -e "${YELLOW}🗑️  Dropping all tables...${NC}"
        
        docker-compose exec mysql mysql -u trader -ptraderpass trading -e "
            SET FOREIGN_KEY_CHECKS = 0;
            DROP TABLE IF EXISTS signals;
            DROP TABLE IF EXISTS signal_aggregation;
            DROP TABLE IF EXISTS signal_history;
            DROP TABLE IF EXISTS symbol_strategies;
            DROP TABLE IF EXISTS threshold_values;
            DROP TABLE IF EXISTS strategy_thresholds;
            DROP TABLE IF EXISTS indicators_macd;
            DROP TABLE IF EXISTS candles_tf;
            DROP TABLE IF EXISTS candles_1m;
            DROP TABLE IF EXISTS trade_strategies;
            DROP TABLE IF EXISTS zones;
            DROP TABLE IF EXISTS indicators;
            DROP TABLE IF EXISTS timeframes;
            DROP TABLE IF EXISTS symbols;
            SET FOREIGN_KEY_CHECKS = 1;
        " 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ All tables dropped successfully!${NC}"
            echo -e "${BLUE}💡 Run ./start.sh to recreate everything${NC}"
        else
            echo -e "${RED}❌ Failed to drop all tables${NC}"
        fi
    else
        echo -e "${BLUE}❌ Operation cancelled${NC}"
    fi
}

# Function to show menu
show_menu() {
    echo ""
    echo "Options:"
    echo "1. Show current database status"
    echo "2. Clear data only (keep table structure)"
    echo "3. Drop data tables (candles, indicators, signals)"
    echo "4. Drop all tables (complete reset)"
    echo "5. Exit"
    echo ""
}

# Main script
case "$1" in
    "status"|"1")
        show_status
        ;;
    "clear"|"2")
        clear_data
        ;;
    "drop-data"|"3")
        drop_data_tables
        ;;
    "drop-all"|"4")
        drop_all_tables
        ;;
    "menu"|"")
        while true; do
            show_menu
            read -p "Select option (1-5): " choice
            case $choice in
                1)
                    show_status
                    ;;
                2)
                    clear_data
                    ;;
                3)
                    drop_data_tables
                    ;;
                4)
                    drop_all_tables
                    ;;
                5)
                    echo "👋 Goodbye!"
                    break
                    ;;
                *)
                    echo -e "${RED}❌ Invalid choice. Please select 1-5.${NC}"
                    ;;
            esac
        done
        ;;
    *)
        echo "Usage: $0 [status|clear|drop-data|drop-all|menu]"
        echo ""
        echo "Commands:"
        echo "  status     - Show current database status"
        echo "  clear      - Clear data only (keep table structure)"
        echo "  drop-data  - Drop data tables only"
        echo "  drop-all   - Drop all tables (complete reset)"
        echo "  menu       - Show interactive menu"
        echo ""
        echo "Examples:"
        echo "  $0 status      # Check current status"
        echo "  $0 clear       # Clear data only"
        echo "  $0 drop-data   # Drop data tables"
        echo "  $0 drop-all    # Complete reset"
        ;;
esac
