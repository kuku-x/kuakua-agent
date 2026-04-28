package com.kuakua.phonestats

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface SessionDao {
    @Query("SELECT * FROM pending_sessions WHERE status = 'PENDING' ORDER BY createdAtMs ASC")
    fun loadPending(): List<SessionEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun upsert(entity: SessionEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    fun upsertAll(entities: List<SessionEntity>)

    @Query("DELETE FROM pending_sessions WHERE status = 'PENDING'")
    fun clearPending()
}

