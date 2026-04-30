# Query Details Propagation Fix

## Problem
The IF node (Check Conversation Exists) was not propagating the `query_details` field from Build SQL Queries node to Get Conversation Details node, causing "Parameter 'query' must be a text string" error.

## Solution
Added a "Merge Queries Data" node that:
1. Receives data from the IF node (when conversation exists)
2. Retrieves all query fields from Build SQL Queries node
3. Merges both data sources
4. Passes complete data to Get Conversation Details

## Flow
```
Build SQL Queries → Get Conversation Count → Check Exists (IF)
                                                    ↓ (true)
                                            Merge Queries Data
                                                    ↓
                                         Get Conversation Details
```

## Implementation
- **New Node**: Merge Queries Data (Code node)
- **Position**: Between IF node and Get Conversation Details
- **Function**: Preserves all query_* fields through the flow

## Testing
1. Send message from existing number
2. Verify count returns 1
3. Verify Get Conversation Details executes without error
4. Check that conversation data is properly retrieved
